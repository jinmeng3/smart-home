from __future__ import annotations

import re
from datetime import timedelta
from hashlib import sha256
from typing import cast
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import case, delete, func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.agents.context import AgentContext
from app.agents.tools.execute.devices import (
    set_curtain_position,
    set_device_power,
    set_device_temperature,
)
from app.models.device import Device, DeviceLog
from app.models.room import Room
from app.models.scene import (
    Scene,
    SceneDraft,
    SceneExecutionLog,
    SceneExecutionStep,
    SceneRoom,
    SceneStep,
    SceneTemplate,
)
from app.schemas.scene import (
    SceneBatchEnabledResult,
    SceneBatchEnabledWrite,
    SceneBatchScheduleResult,
    SceneBatchScheduleWrite,
    SceneDraftRead,
    SceneDraftWrite,
    SceneExecutionRead,
    SceneExecutionStepRead,
    SceneListRead,
    SceneLogListRead,
    SceneLogRead,
    SceneOrderRead,
    SceneOrderWrite,
    ScenePreviewRead,
    ScenePreviewStep,
    SceneRead,
    SceneStepRead,
    SceneSummaryRead,
    SceneTemplateListRead,
    SceneTemplatePreviewRead,
    SceneTemplatePreviewStep,
    SceneTemplateRead,
    SceneTemplateUseWrite,
    SceneWrite,
    TriggerType,
)
from app.utils.db import count_query, get_or_404
from app.utils.json import dump_json, parse_json_list
from app.utils.time import now_utc

HIGH_RISK_KEYWORDS = ("lock", "camera", "门锁", "摄像头", "安防")


# === 场景管理 ===


def get_scene_or_404(db: Session, household_id: int, scene_id: str) -> Scene:
    return get_or_404(
        db,
        select(Scene)
        .options(selectinload(Scene.steps))
        .where(Scene.household_id == household_id, Scene.id == scene_id),
        detail="场景不存在",
    )


def get_template_or_404(db: Session, template_id: str) -> SceneTemplate:
    template = get_or_404(
        db,
        select(SceneTemplate).where(SceneTemplate.id == template_id),
        detail="场景模板不存在",
    )
    if not template.enabled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="场景模板不存在"
        )
    return template


def serialize_scene(scene: Scene) -> SceneRead:
    return SceneRead(
        id=scene.id,
        name=scene.name,
        description=scene.description,
        icon=scene.icon,
        color=scene.color,
        trigger_type=cast(TriggerType, scene.trigger_type),
        trigger_label=scene.trigger_label,
        room_labels=parse_json_list(scene.room_names),
        device_count=scene.device_count,
        enabled=scene.enabled,
        recommended=scene.recommended,
        high_risk=scene.high_risk,
        sort_order=scene.sort_order,
        source_template_id=scene.source_template_id,
        created_at=scene.created_at,
        updated_at=scene.updated_at,
        steps=[
            {
                "id": step.id,
                "name": step.name,
                "description": step.description,
                "device_id": step.device_id,
                "order": step.step_order,
                "action": step.action,
                "action_value": step.action_value,
            }
            for step in sorted(scene.steps, key=lambda item: item.step_order)
        ],
    )


def apply_scene_payload(scene: Scene, payload: SceneWrite) -> None:
    scene.name = payload.name
    scene.description = payload.description
    scene.icon = payload.icon
    scene.color = payload.color
    scene.trigger_type = payload.trigger_type
    scene.trigger_label = payload.trigger_label
    scene.room_names = dump_json(payload.room_labels)
    device_ids = set(payload.device_ids) | {step.device_id for step in payload.steps}
    scene.device_count = len(device_ids)
    scene.enabled = payload.enabled
    scene.recommended = payload.recommended
    values = [payload.name, *(step.device_id for step in payload.steps)]
    scene.high_risk = (
        payload.high_risk
        if payload.high_risk is not None
        else any(
            keyword in value.lower()
            for value in values
            for keyword in HIGH_RISK_KEYWORDS
        )
    )
    scene.updated_at = now_utc()


def replace_steps(scene: Scene, payload: SceneWrite) -> None:
    scene.steps.clear()
    scene.steps.extend(
        SceneStep(
            id=f"{scene.id}-{step.order}-{uuid4().hex[:6]}",
            name=step.name,
            description=step.description,
            device_id=step.device_id,
            step_order=step.order,
            action=step.action,
            action_value=step.action_value,
        )
        for step in sorted(payload.steps, key=lambda item: item.order)
    )


def get_scenes_service(
    db: Session,
    household_id: int,
    keyword: str | None,
    trigger_type: str | None,
    enabled: str,
    room_id: int | None = None,
) -> SceneListRead:
    filters = [Scene.household_id == household_id]
    if keyword and keyword.strip():
        term = f"%{keyword.strip()}%"
        filters.append(
            or_(
                Scene.name.like(term),
                Scene.description.like(term),
                Scene.trigger_label.like(term),
            )
        )
    if trigger_type:
        filters.append(Scene.trigger_type == trigger_type)
    if enabled == "enabled":
        filters.append(Scene.enabled.is_(True))
    elif enabled == "disabled":
        filters.append(Scene.enabled.is_(False))

    query = select(Scene)
    if room_id is not None:
        query = query.join(SceneRoom, SceneRoom.scene_id == Scene.id).where(
            SceneRoom.room_id == room_id
        )
    scenes = db.scalars(
        query.options(selectinload(Scene.steps))
        .where(*filters)
        .order_by(Scene.sort_order, Scene.updated_at.desc())
    ).all()
    return SceneListRead(
        items=[serialize_scene(scene) for scene in scenes], total=len(scenes)
    )


def replace_scene_rooms(
    db: Session, scene: Scene, household_id: int, room_labels: list[str]
) -> None:
    labels = set(room_labels)
    rooms = (
        list(
            db.scalars(
                select(Room).where(
                    Room.household_id == household_id,
                    Room.name.in_(labels),
                )
            )
        )
        if labels
        else []
    )
    found_labels = {room.name for room in rooms}
    if found_labels != labels:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "message": "部分房间不存在",
                "rooms": sorted(labels - found_labels),
            },
        )
    db.execute(delete(SceneRoom).where(SceneRoom.scene_id == scene.id))
    db.add_all([SceneRoom(scene_id=scene.id, room_id=room.id) for room in rooms])


def add_scene_service(
    db: Session, household_id: int, user_id: int, payload: SceneWrite
) -> SceneRead:
    base_id = re.sub(r"[^a-z0-9]+", "-", payload.name.lower()).strip("-")[:40]
    base_id = base_id or "scene"
    scene_id = base_id
    while db.scalar(
        select(Scene.id).where(Scene.household_id == household_id, Scene.id == scene_id)
    ):
        scene_id = f"{base_id}-{uuid4().hex[:8]}"
    scene = Scene(
        id=scene_id,
        household_id=household_id,
        created_by=user_id,
    )
    apply_scene_payload(scene, payload)
    replace_steps(scene, payload)
    db.add(scene)
    replace_scene_rooms(db, scene, household_id, payload.room_labels)
    scene.sort_order = (
        db.scalar(
            select(func.max(Scene.sort_order)).where(Scene.household_id == household_id)
        )
        or 0
    )
    scene.sort_order += 10
    db.commit()
    db.refresh(scene)
    return serialize_scene(get_scene_or_404(db, household_id, scene.id))


def edit_scene_service(
    db: Session, household_id: int, scene_id: str, payload: SceneWrite
) -> SceneRead:
    scene = get_scene_or_404(db, household_id, scene_id)
    apply_scene_payload(scene, payload)
    replace_steps(scene, payload)
    replace_scene_rooms(db, scene, household_id, payload.room_labels)
    db.commit()
    return serialize_scene(get_scene_or_404(db, household_id, scene.id))


def change_enabled_service(
    db: Session, household_id: int, scene_id: str, enabled: bool
) -> Scene:
    scene = get_scene_or_404(db, household_id, scene_id)
    scene.enabled = enabled
    scene.updated_at = now_utc()
    db.commit()
    db.refresh(scene)
    return scene


# === 场景执行 ===


def run_scene_service(
    db: Session,
    household_id: int,
    scene_id: str,
    confirm_high_risk: bool,
    source: str,
    executed_by: int,
    session_id: int = 0,
    auto_execute_low_risk: bool = True,
    idempotency_key: str | None = None,
) -> SceneExecutionRead:
    """执行场景，支持幂等键以避免重复执行。

    Args:
        db: 数据库会话。
        household_id: 家庭 ID。
        scene_id: 场景 ID。
        confirm_high_risk: 是否确认高风险操作。
        source: 触发来源（manual / agent / room）。
        executed_by: 执行人 user_id。用于构造 AgentContext 调 set_device_*
            （DeviceLog 会记录该用户）。
        session_id: 会话 ID。Agent 路径填真实会话，其他填 0。
        auto_execute_low_risk: 是否允许跳过高风险审批（场景已在调用前完成高风险确认，
            这里主要用于控制 log 的 status 字段）。
        idempotency_key: 幂等键。agent 场景执行时传入 approval_id 以实现幂等。

    Returns:
        SceneExecutionRead: 执行记录。
    """
    scene = get_scene_or_404(db, household_id, scene_id)
    if scene.high_risk and not confirm_high_risk:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="该场景包含高风险动作，请确认后执行",
        )
    if not scene.enabled:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="场景已停用")

    started_at = now_utc()

    if idempotency_key:
        digest = sha256(
            f"{household_id}:{scene_id}:{idempotency_key}".encode()
        ).hexdigest()[:48]
        execution_id = f"exec-agent-{digest}"

        existing = db.get(SceneExecutionLog, execution_id)
        if existing is not None:
            return serialize_execution(existing)
    else:
        execution_id = f"exec-{started_at:%Y%m%d%H%M%S}-{uuid4().hex[:8]}"

    is_agent_execution = source == "agent"

    # 调设备需要 AgentContext，household_id + user_id 必要。
    exec_context = AgentContext(
        user_id=executed_by,
        household_id=household_id,
        session_id=session_id,
        auto_execute_low_risk=auto_execute_low_risk,
        confirm_high_risk=confirm_high_risk,
    )

    # 逐个 step 执行写操作。失败时记录到 log，但不回滚已成功的 step
    # （set_* 函数内部已 commit，无法回滚；这是与 Agent 路径同源的语义）。
    sorted_steps = sorted(scene.steps, key=lambda item: item.step_order)
    step_results: list[tuple[SceneStep, str, str]] = []
    for step in sorted_steps:
        if step.action == "noop":
            step_results.append((step, "completed", "noop"))
            continue
        # NULL action：查 DeviceLog 最近一条以推断取反动作，
        # 遵循用户选择的 A3 语义（按设备历史动作取反）。
        # 历史数据 NULL = fallback "on"（开）。
        inferred_value: float | None = None
        if step.action is None:
            inferred = _infer_action_from_log(db, step.device_id)
            if inferred is None:
                # 无 DeviceLog 或最近动作为 set_temperature（不可取反）
                step_results.append(
                    (step, "skipped", "无历史动作可推断且未配置 action")
                )
                continue
            action, inferred_value = inferred
        else:
            action = step.action
        ok, msg = _dispatch_step(db, exec_context, step, action, inferred_value)
        step_results.append((step, "completed" if ok else "failed", msg))

    has_failure = any(
        status_ in ("failed", "skipped") for _, status_, _ in step_results
    )
    final_status = (
        "submitted"
        if is_agent_execution
        else ("failed" if has_failure else "completed")
    )
    final_message = (
        "已提交到业务执行层，等待设备状态回读"
        if is_agent_execution
        else ("部分步骤失败" if has_failure else "执行成功")
    )

    log = SceneExecutionLog(
        id=execution_id,
        scene_id=scene.id,
        status=final_status,
        source=source,
        started_at=started_at,
        finished_at=None if is_agent_execution else started_at,
        message=final_message,
    )
    log.steps = [
        SceneExecutionStep(
            id=f"{execution_id}-{index}",
            step_id=step.id,
            status=status_,
            started_at=started_at,
            finished_at=None if is_agent_execution else started_at,
            message=msg,
        )
        for index, (step, status_, msg) in enumerate(step_results, 1)
    ]
    scene.monthly_execute_count += 1
    scene.last_executed_at = started_at
    scene.updated_at = started_at
    db.add(log)
    db.commit()
    return serialize_execution(log)


def _infer_action_from_log(
    db: Session, device_id_str: str
) -> tuple[str, float | None] | None:
    """根据设备最近一次 DeviceLog 推断“取反”动作（A3 语义）。

    Returns:
        - ``(action, value)``：推断出的 step action（已取反）；set_position 类
          同时返回 position value。
        - ``None``：无 DeviceLog 或最近动作为 set_temperature（不可取反）。

    映射：
        power_on  -> ("off", None)       关
        power_off -> ("on",  None)       开
        curtain_open  -> ("set_position", 0)    全关
        curtain_close -> ("set_position", 100)  全开
        set_temperature -> None（不取反）
    """
    last = db.scalar(
        select(DeviceLog)
        .where(DeviceLog.device_id == device_id_str)
        .order_by(DeviceLog.created_at.desc())
        .limit(1)
    )
    if last is None:
        return None
    if last.action == "power_on":
        return ("off", None)
    if last.action == "power_off":
        return ("on", None)
    if last.action == "curtain_open":
        return ("set_position", 0)
    if last.action == "curtain_close":
        return ("set_position", 100)
    # set_temperature / 其他未知动作：不可取反
    return None


def _dispatch_step(
    db: Session,
    context: AgentContext,
    step: SceneStep,
    action: str,
    action_value: float | None = None,
) -> tuple[bool, str]:
    """按 step.action 调对应的 set_device_* 函数。

    返回 ``(ok, message)``。失败时 message 包含原因。函数不抛异常
    （底层 set_* 已自行 rollback）。
    """
    device = db.scalar(
        select(Device).where(
            Device.device_id == step.device_id,
            Device.household_id == context.household_id,
        )
    )
    if device is None:
        return False, f"设备不存在：{step.device_id}"

    if action in ("on", "off"):
        result = set_device_power(
            db,
            context,
            device_id=device.id,
            power=action,
        )
    elif action == "set_temperature":
        # 优先用 caller 传入的 value（用于 A3 推断），回退到 step 持久化的值
        value = action_value if action_value is not None else step.action_value
        if value is None:
            return False, "set_temperature 缺少 action_value"
        result = set_device_temperature(
            db,
            context,
            device_id=device.id,
            temperature=float(value),
        )
    elif action == "set_position":
        # 同上
        value = action_value if action_value is not None else step.action_value
        if value is None:
            return False, "set_position 缺少 action_value"
        result = set_curtain_position(
            db,
            context,
            device_id=device.id,
            position=int(value),
        )
    else:
        return False, f"未知 action：{action}"

    if not result.get("ok", False):
        return False, str(
            result.get("message") or result.get("error") or "设备操作失败"
        )
    return True, str(result.get("message", f"{step.name} 执行成功"))


def serialize_execution(log: SceneExecutionLog) -> SceneExecutionRead:
    return SceneExecutionRead(
        execution_id=log.id,
        scene_id=log.scene_id,
        status=log.status,
        started_at=log.started_at,
        finished_at=log.finished_at,
        steps=[
            SceneExecutionStepRead(
                step_id=step.step_id, status=step.status, message=step.message
            )
            for step in log.steps
        ],
    )


def duplicate_scene_service(
    db: Session, household_id: int, user_id: int, scene_id: str, name: str
) -> SceneRead:
    source = get_scene_or_404(db, household_id, scene_id)
    payload = SceneWrite(
        name=name,
        description=source.description,
        icon=source.icon,
        color=source.color,
        trigger_type=cast(TriggerType, source.trigger_type),
        trigger_label=source.trigger_label,
        room_labels=parse_json_list(source.room_names),
        enabled=source.enabled,
        recommended=False,
        high_risk=source.high_risk,
        steps=[
            {
                "name": step.name,
                "description": step.description,
                "device_id": step.device_id,
                "order": step.step_order,
            }
            for step in source.steps
        ],
    )
    return add_scene_service(db, household_id, user_id, payload)


def remove_scene_service(db: Session, household_id: int, scene_id: str) -> None:
    """删除场景及其执行步骤、执行日志（ORM 级联清理辅助表）。"""
    scene = get_scene_or_404(db, household_id, scene_id)
    db.delete(scene)
    db.commit()


def get_logs_service(
    db: Session, household_id: int, scene_id: str, limit: int
) -> SceneLogListRead:
    get_scene_or_404(db, household_id, scene_id)
    logs = db.scalars(
        select(SceneExecutionLog)
        .where(SceneExecutionLog.scene_id == scene_id)
        .order_by(SceneExecutionLog.started_at.desc())
        .limit(limit)
    ).all()
    return SceneLogListRead(
        items=[SceneLogRead.model_validate(log, from_attributes=True) for log in logs]
    )


def get_summary_service(db: Session, household_id: int) -> SceneSummaryRead:
    total, enabled, manual = db.execute(
        select(
            func.count(Scene.id),
            func.count().filter(Scene.enabled.is_(True)),
            func.count().filter(Scene.trigger_type == "manual"),
        ).where(Scene.household_id == household_id)
    ).one()
    automation = total - manual
    now = now_utc()
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    next_month_start = (
        month_start.replace(year=month_start.year + 1, month=1)
        if month_start.month == 12
        else month_start.replace(month=month_start.month + 1)
    )
    previous_month_start = (month_start - timedelta(days=1)).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    monthly, previous_monthly = db.execute(
        select(
            func.count().filter(
                SceneExecutionLog.started_at >= month_start,
                SceneExecutionLog.started_at < next_month_start,
            ),
            func.count().filter(
                SceneExecutionLog.started_at >= previous_month_start,
                SceneExecutionLog.started_at < month_start,
            ),
        )
        .select_from(SceneExecutionLog)
        .join(Scene, Scene.id == SceneExecutionLog.scene_id)
        .where(Scene.household_id == household_id)
    ).one()
    monthly_growth_rate = (
        round((monthly - previous_monthly) * 100 / previous_monthly, 1)
        if previous_monthly
        else (100.0 if monthly else 0.0)
    )
    return SceneSummaryRead(
        enabled=enabled,
        automation=automation,
        manual=manual,
        monthly_executions=monthly,
        enabled_rate=round(enabled * 100 / total, 1) if total else 0,
        automation_rate=round(automation * 100 / total, 1) if total else 0,
        manual_rate=round(manual * 100 / total, 1) if total else 0,
        monthly_growth_rate=monthly_growth_rate,
    )


def reorder_scenes_service(
    db: Session, household_id: int, payload: SceneOrderWrite
) -> SceneOrderRead:
    ids = [item.id for item in payload.items]
    found_ids = set(
        db.scalars(
            select(Scene.id).where(
                Scene.household_id == household_id, Scene.id.in_(ids)
            )
        )
    )
    missing = set(ids) - found_ids
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="部分场景不存在"
        )
    order_by_id = {item.id: item.sort_order for item in payload.items}
    db.execute(
        update(Scene)
        .where(Scene.household_id == household_id, Scene.id.in_(ids))
        .values(sort_order=case(order_by_id, value=Scene.id))
    )
    db.commit()
    return SceneOrderRead(updated=len(payload.items))


def get_scene_preview_service(
    db: Session, household_id: int, scene_id: str
) -> ScenePreviewRead:
    scene = get_scene_or_404(db, household_id, scene_id)
    return ScenePreviewRead(
        scene_id=scene.id,
        high_risk=scene.high_risk,
        trigger_label=scene.trigger_label,
        steps=[
            ScenePreviewStep(
                step_id=step.id,
                name=step.name,
                device_id=step.device_id,
                estimated_ms=300,
                risk_level=(
                    "high"
                    if any(
                        word in step.device_id.lower() for word in HIGH_RISK_KEYWORDS
                    )
                    else "low"
                ),
            )
            for step in scene.steps
        ],
    )


def get_execution_service(
    db: Session, household_id: int, scene_id: str
) -> SceneExecutionRead:
    scene = get_scene_or_404(db, household_id, scene_id)
    execution = db.scalar(
        select(SceneExecutionLog)
        .where(SceneExecutionLog.scene_id == scene.id)
        .order_by(SceneExecutionLog.started_at.desc())
    )
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="暂无执行记录"
        )
    return serialize_execution(execution)


# === 场景草稿 ===


def add_draft_service(
    db: Session, household_id: int, user_id: int, payload: SceneDraftWrite
) -> SceneDraftRead:
    """保存场景表单快照。"""
    draft_id = f"draft-{uuid4().hex[:12]}"
    draft = SceneDraft(
        id=draft_id,
        household_id=household_id,
        created_by=user_id,
        payload_json=payload.model_dump_json(),
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return SceneDraftRead(draft_id=draft.id, updated_at=draft.updated_at)


# === 场景模板 ===


def get_templates_service(
    db: Session, keyword: str | None, category: str | None, limit: int
) -> SceneTemplateListRead:
    """按关键字、分类读取可用模板。"""
    filters = [SceneTemplate.enabled.is_(True)]
    if keyword and keyword.strip():
        term = f"%{keyword.strip()}%"
        filters.append(
            or_(
                SceneTemplate.name.like(term),
                SceneTemplate.description.like(term),
            )
        )
    if category:
        filters.append(SceneTemplate.category == category)
    templates = db.scalars(
        select(SceneTemplate)
        .where(*filters)
        .order_by(SceneTemplate.sort_order, SceneTemplate.updated_at.desc())
        .limit(limit)
    ).all()

    items = []
    for t in templates:
        steps_data = parse_json_list(t.steps_json)
        steps: list[SceneStepRead] = []
        for i, s in enumerate(steps_data):
            # 模板里 step 字段可能缺失（生产历史数据），降级到合法值避免整个
            # ``/api/scenes/templates`` 返 500。Pydantic SceneStepRead 要求
            # name/device_id 非空、order ≥ 1。
            step_name = (s.get("name") or "").strip() or f"步骤 {i + 1}"
            step_device_id = (s.get("device_id") or "").strip() or f"unknown-{i}"
            try:
                step_order = int(s.get("order", i + 1))
            except (TypeError, ValueError):
                step_order = i + 1
            if step_order < 1:
                step_order = i + 1
            steps.append(
                SceneStepRead(
                    id=f"{t.id}-{i}",
                    name=step_name[:120],
                    description=(s.get("description") or "")[:500],
                    device_id=step_device_id[:120],
                    order=step_order,
                )
            )
        items.append(
            SceneTemplateRead(
                id=t.id,
                name=t.name,
                description=t.description,
                icon=t.icon,
                color=t.color,
                trigger_type=cast(TriggerType, t.trigger_type),
                trigger_label=t.trigger_label,
                room_labels=parse_json_list(t.room_labels),
                device_count=t.device_count,
                recommended=t.recommended,
                category=t.category,
                steps=steps,
            )
        )
    return SceneTemplateListRead(items=items)


def get_template_preview_service(
    db: Session, household_id: int, template_id: str
) -> SceneTemplatePreviewRead:
    """预览模板步骤及本地设备匹配情况。"""
    template = get_template_or_404(db, template_id)
    steps_data = parse_json_list(template.steps_json)

    template_device_ids = {
        s.get("device_id", "") for s in steps_data if s.get("device_id")
    }

    household_device_ids = (
        set(
            db.scalars(
                select(Device.device_id).where(
                    Device.household_id == household_id,
                    Device.device_id.in_(template_device_ids),
                )
            )
        )
        if template_device_ids
        else set()
    )

    preview_steps = []
    for s in steps_data:
        device_id = s.get("device_id", "")
        preview_steps.append(
            SceneTemplatePreviewStep(
                name=s.get("name", ""),
                description=s.get("description", ""),
                device_id=device_id,
                matched=device_id in household_device_ids,
            )
        )

    matched_count = sum(1 for step in preview_steps if step.matched)
    missing_count = len(preview_steps) - matched_count

    return SceneTemplatePreviewRead(
        template_id=template.id,
        matched_device_count=matched_count,
        missing_device_count=missing_count,
        steps=preview_steps,
    )


def import_template_service(
    db: Session,
    household_id: int,
    user_id: int,
    template_id: str,
    payload: SceneTemplateUseWrite,
) -> SceneRead:
    """复制模板数据并创建可编辑场景。"""
    template = get_template_or_404(db, template_id)
    steps_data = parse_json_list(template.steps_json)
    device_mapping = payload.device_mapping or {}

    scene_payload = SceneWrite(
        name=payload.name or template.name,
        description=template.description,
        icon=template.icon,
        color=template.color,
        trigger_type=cast(TriggerType, template.trigger_type),
        trigger_label=template.trigger_label,
        room_labels=parse_json_list(template.room_labels),
        device_ids=[],
        enabled=payload.enabled,
        recommended=False,
        steps=[
            {
                "name": s.get("name", ""),
                "description": s.get("description", ""),
                "device_id": device_mapping.get(
                    s.get("device_id", ""), s.get("device_id", "")
                ),
                "order": s.get("order", i + 1),
            }
            for i, s in enumerate(steps_data)
        ],
    )
    return add_scene_service(db, household_id, user_id, scene_payload)


# === 批量操作 ===


def batch_change_enabled_service(
    db: Session, household_id: int, payload: SceneBatchEnabledWrite
) -> SceneBatchEnabledResult:
    """批量启用或停用场景。"""
    filters = [Scene.household_id == household_id]
    if payload.scene_ids:
        filters.append(Scene.id.in_(payload.scene_ids))
    count = count_query(db, select(Scene).where(*filters))
    db.execute(
        update(Scene)
        .where(*filters)
        .values(enabled=payload.enabled, updated_at=now_utc())
    )
    db.commit()
    return SceneBatchEnabledResult(updated_count=count)


def batch_set_schedule_service(
    db: Session, household_id: int, payload: SceneBatchScheduleWrite
) -> SceneBatchScheduleResult:
    """批量设置场景的触发类型和定时描述。"""
    filters = [Scene.household_id == household_id]
    if payload.scene_ids:
        filters.append(Scene.id.in_(payload.scene_ids))
    count = count_query(db, select(Scene).where(*filters))
    db.execute(
        update(Scene)
        .where(*filters)
        .values(
            trigger_type=payload.trigger_type,
            trigger_label=payload.trigger_label,
            updated_at=now_utc(),
        )
    )
    db.commit()
    return SceneBatchScheduleResult(updated_count=count)
