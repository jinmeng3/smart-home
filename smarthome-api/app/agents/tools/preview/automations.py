from app.agents.context import AgentContext
from app.agents.errors import AgentToolExecutionError
from app.models.automation import Automation, AutomationAction
from app.services.automation import get_automation as get_automation_service
from fastapi import HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class PreviewAutomationChangeInput(BaseModel):
    """预览自动化变更的参数。automation_id 和 proposed_* 至少提供一个。"""

    automation_id: int | None = None
    proposed_name: str | None = Field(default=None, max_length=30)
    proposed_triggers: list[dict] | None = None
    proposed_conditions: list[dict] | None = None
    proposed_actions: list[dict] | None = None


def preview_automation_change(
    db: Session,
    context: AgentContext,
    automation_id=None,
    proposed_name=None,
    proposed_triggers=None,
    proposed_conditions=None,
    proposed_actions=None,
):
    """预览自动化变更的影响范围，不实际修改任何数据。返回当前配置与变更后的对比。"""
    current = None
    if automation_id is not None:
        try:
            automation = get_automation_service(db, automation_id, context.household_id)
            current = {
                "id": automation.id,
                "name": automation.name,
                "description": automation.description,
                "trigger_type": automation.trigger_type,
                "enabled": automation.enabled,
                "priority": automation.priority,
                "version": automation.version,
                "triggers": [
                    {"type": t.type, "config": t.config_json}
                    for t in automation.triggers
                ],
                "conditions": [
                    {"type": c.type, "config": c.config_json}
                    for c in automation.conditions
                ],
                "actions": [
                    {
                        "type": a.type,
                        "config": a.config_json,
                        "device_id": a.device_id,
                        "scene_id": a.scene_id,
                    }
                    for a in automation.actions
                ],
            }
        except HTTPException as exc:
            raise AgentToolExecutionError(str(exc.detail)) from exc

    proposed = {}
    if proposed_name is not None:
        proposed["name"] = proposed_name
    if proposed_triggers is not None:
        proposed["triggers"] = proposed_triggers
    if proposed_conditions is not None:
        proposed["conditions"] = proposed_conditions
    if proposed_actions is not None:
        proposed["actions"] = proposed_actions

    # 计算变更摘要
    changed_fields = []
    if current and proposed:
        for key, value in proposed.items():
            if key in current and str(value) != str(current[key]):
                changed_fields.append(key)
    elif proposed:
        changed_fields = list(proposed.keys())

    return {
        "status": "previewed",
        "has_changes": len(changed_fields) > 0,
        "changed_fields": changed_fields,
        "current": current,
        "proposed": proposed if proposed else None,
        "device_count": (
            len(
                {
                    a.get("device_id")
                    for a in (proposed.get("actions") or [])
                    if a.get("device_id")
                }
            )
            if proposed.get("actions")
            else (current.get("device_count", 0) if current else 0)
        ),
    }


class DetectAutomationConflictsInput(BaseModel):
    """检测自动化冲突的参数。"""

    automation_id: int | None = Field(default=None)
    proposed_triggers: list[dict] | None = None
    proposed_actions: list[dict] | None = None


def detect_automation_conflicts(
    db: Session,
    context: AgentContext,
    automation_id=None,
    proposed_triggers=None,
    proposed_actions=None,
):
    """检测自动化规则之间是否存在时间重叠、设备冲突或循环触发风险。"""
    conflicts = []

    # 获取当前家庭的所有自动化
    automations = db.scalars(
        select(Automation).where(Automation.household_id == context.household_id)
    ).all()

    # 排除自身
    others = [a for a in automations if a.id != automation_id]

    # 解析待检测的触发器
    triggers_to_check = proposed_triggers or []
    actions_to_check = proposed_actions or []
    if automation_id is not None:
        try:
            current = get_automation_service(db, automation_id, context.household_id)
            if not triggers_to_check:
                triggers_to_check = [
                    {"type": t.type, "config": t.config_json}
                    for t in current.triggers
                ]
            if not actions_to_check:
                actions_to_check = [
                    {
                        "type": action.type,
                        "config": action.config_json,
                        "device_id": action.device_id,
                    }
                    for action in current.actions
                ]
        except HTTPException:
            pass

    # 检查时间重叠（schedule 类型）
    schedule_triggers = [
        t for t in triggers_to_check if t.get("type") == "schedule"
    ]
    for st in schedule_triggers:
        raw_config = st.get("config", {})
        if isinstance(raw_config, str):
            try:
                import json
                st_config = json.loads(raw_config)
            except (json.JSONDecodeError, TypeError):
                continue
        else:
            st_config = raw_config
        st_time = st_config.get("time") if isinstance(st_config, dict) else None
        st_days = set(st_config.get("days", []) or []) if isinstance(st_config, dict) else set()
        for other in others:
            for ot in other.triggers:
                if ot.type == "schedule":
                    ot_config = ot.config_json
                    try:
                        import json

                        ot_config_dict = json.loads(ot_config)
                    except (json.JSONDecodeError, TypeError):
                        continue
                    ot_time = ot_config_dict.get("time")
                    ot_days = set(ot_config_dict.get("days", []) or [])
                    if st_time == ot_time and (not st_days or st_days & ot_days):
                        conflicts.append(
                            {
                                "type": "schedule_overlap",
                                "severity": "warning",
                                "message": f"与自动化「{other.name}」在同一时间 {st_time} 触发",
                                "target_automation_id": other.id,
                                "target_automation_name": other.name,
                            }
                        )

    # 检查同一设备动作冲突与设备触发回路。
    trigger_device_ids = set()
    for t in triggers_to_check:
        config = t.get("config", {})
        if isinstance(config, str):
            try:
                import json

                config = json.loads(config)
            except (json.JSONDecodeError, TypeError):
                continue
        device_id = config.get("device_id")
        if device_id is not None:
            trigger_device_ids.add(device_id)

    # 检查动作设备冲突
    all_actions = list(
        db.scalars(
            select(AutomationAction).where(
                AutomationAction.automation_id.in_(
                    select(Automation.id).where(
                        Automation.household_id == context.household_id
                    )
                )
            )
        ).all()
    )
    action_device_map: dict[int, set[int]] = {}
    for action in all_actions:
        if action.device_id is not None:
            action_device_map.setdefault(action.automation_id, set()).add(
                action.device_id
            )

    proposed_action_device_ids = {
        action.get("device_id")
        for action in actions_to_check
        if action.get("device_id") is not None
    }
    for other in others:
        shared_ids = proposed_action_device_ids & action_device_map.get(other.id, set())
        if shared_ids:
            conflicts.append(
                {
                    "type": "device_action_overlap",
                    "severity": "warning",
                    "message": f"与自动化「{other.name}」操作了相同设备",
                    "device_ids": sorted(shared_ids),
                    "target_automation_id": other.id,
                    "target_automation_name": other.name,
                }
            )

    loop_device_ids = trigger_device_ids & proposed_action_device_ids
    if loop_device_ids:
        conflicts.append(
            {
                "type": "possible_trigger_loop",
                "severity": "high",
                "message": "同一规则读取并操作相同设备，可能形成循环触发",
                "device_ids": sorted(loop_device_ids),
            }
        )

    return {
        "status": "checked",
        "conflict_count": len(conflicts),
        "conflicts": conflicts,
        "summary": (
            "未检测到冲突"
            if not conflicts
            else f"发现 {len(conflicts)} 个潜在冲突"
        ),
    }