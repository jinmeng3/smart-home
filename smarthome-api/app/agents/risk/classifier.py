from app.agents.context import AgentContext
from app.agents.risk.policy import RiskDecision, RiskLevel
from app.models.device import Device
from app.services.automation import get_automation as get_automation_svc
from app.services.scene import get_scene_or_404
from sqlalchemy import select
from sqlalchemy.orm import Session

HIGH_RISK_DEVICE_TYPES = {
    "lock",
    "door_lock",
    "camera",
    "security",
    "alarm",
}
HIGH_RISK_KEYWORDS = {
    "lock",
    "camera",
    "security",
    "alarm",
    "门锁",
    "摄像头",
    "安防",
    "警报",
}


def _is_high_risk_device(device: Device) -> bool:
    values = (
        device.device_id.lower(),
        device.name.lower(),
        device.type.lower(),
    )
    return device.type.lower() in HIGH_RISK_DEVICE_TYPES or any(
        keyword in value for keyword in HIGH_RISK_KEYWORDS for value in values
    )


def classify_automation_operation(
    db: Session,
    context: AgentContext,
    operation: str,
    automation_id: int | None = None,
    actions: list[dict] | None = None,
    args: dict | None = None,
) -> RiskDecision:
    """分类自动化操作的风险等级。

    Args:
        operation: 操作类型 (create_automation / update_automation / set_automation_enabled / delete_automation)
        automation_id: 自动化规则 ID（创建时可为 None）
        actions: 动作列表（仅创建/更新时需要）
        args: 完整参数字典（用于构建丰富的预览信息）
    """
    reasons: list[str] = []
    resource_version = ""

    if automation_id is not None:
        automation = get_automation_svc(db, automation_id, context.household_id)
        resource_version = str(automation.version)

    if operation == "delete_automation":
        level = RiskLevel.HIGH
        reasons.append("删除自动化规则可能影响家庭自动化流程")

    elif operation == "set_automation_enabled":
        level = RiskLevel.LOW
        reasons.append("仅切换自动化规则的启用状态")

    elif operation in ("create_automation", "update_automation"):
        action_devices = []
        requested_device_ids = {
            a.get("device_id")
            for a in (actions or [])
            if a.get("device_id") is not None
        }
        # 递归解析动作中的 scene 引用：通过场景间接控制的设备同样参与风险判定（§5.5）
        expanded_scene_device_ids: set[int] = set()
        scene_refs = [a for a in (actions or []) if a.get("scene_id")]
        if scene_refs:
            from app.models.scene import Scene, SceneStep

            scene_rows = db.scalars(
                select(Scene).where(
                    Scene.household_id == context.household_id,
                    Scene.id.in_({str(a["scene_id"]) for a in scene_refs}),
                )
            ).all()
            if len(scene_rows) != len({str(a["scene_id"]) for a in scene_refs}):
                requested_device_ids.add(
                    -1
                )  # 标记存在不存在/跨家庭场景（校正为未知名）
                missing_scene = True
            else:
                missing_scene = False

                if scene_rows:
                    steps = db.scalars(
                        select(SceneStep).where(
                            SceneStep.scene_id.in_([s.id for s in scene_rows])
                        )
                    ).all()
                    expanded_scene_device_ids = {
                        int(step.device_id)
                        for step in steps
                        if step.device_id is not None
                        and str(step.device_id).lstrip("-").isdigit()
                    }
                    requested_device_ids.update(expanded_scene_device_ids)
        else:
            missing_scene = False

        if requested_device_ids:
            action_devices = list(
                db.scalars(
                    select(Device).where(
                        Device.household_id == context.household_id,
                        Device.id.in_(requested_device_ids),
                    )
                ).all()
            )

        found_device_ids = {device.id for device in action_devices}
        missing_device_ids = requested_device_ids - found_device_ids
        high_risk_devices = [d for d in action_devices if _is_high_risk_device(d)]
        if scene_refs and missing_scene:
            missing_device_ids.add(-1)

        if missing_device_ids:
            level = RiskLevel.UNKNOWN
            reasons.append("动作包含不存在或不属于当前家庭的设备或场景")
        elif high_risk_devices:
            level = RiskLevel.HIGH
            reasons.append(
                "包含高风险设备：" + "、".join(d.name for d in high_risk_devices)
            )
        else:
            level = RiskLevel.LOW
            reasons.append("仅包含已识别的普通家居设备操作")

        if expanded_scene_device_ids:
            reasons.append("动作包含场景引用，已展开场景步骤设备参与风险判定")

    else:
        level = RiskLevel.UNKNOWN
        reasons.append(f"未知的自动化操作类型：{operation}")

    preview: dict = {
        "kind": operation,
        "operation": operation,
        "automation_id": automation_id,
        "risk_level": level.value,
    }

    if operation == "create_automation" and args:
        preview["automation_name"] = args.get("name", "")
        preview["trigger_count"] = len(args.get("triggers", []))
        preview["condition_count"] = len(args.get("conditions", []))
        preview["action_count"] = len(args.get("actions", []))
        preview["summary"] = f"创建自动化规则：{args.get('name', '（未命名）')}"
        if action_devices:
            preview["affected_device_names"] = [d.name for d in action_devices]

    elif operation == "update_automation" and automation_id is not None and args:
        preview["automation_name"] = automation.name
        changed_fields = []
        field_map = {
            "name": "名称",
            "triggers": "触发器",
            "conditions": "条件",
            "actions": "动作",
            "priority": "优先级",
            "cooldown_seconds": "冷却时间",
            "delay_seconds": "延迟时间",
        }
        for field, label in field_map.items():
            if field in args and args[field] is not None:
                changed_fields.append(label)
        preview["changed_fields"] = changed_fields
        preview["summary"] = f"修改自动化规则：{automation.name}"

    # 对创建/更新自动化，将冲突检测结果纳入预览（§5.5）
    if operation in ("create_automation", "update_automation") and args:
        try:
            from app.agents.tools.preview.automations import detect_automation_conflicts

            conflicts = detect_automation_conflicts(
                db=db,
                context=context,
                automation_id=automation_id,
                proposed_triggers=args.get("triggers"),
                proposed_actions=args.get("actions"),
            )
            if conflicts:
                preview["conflicts"] = conflicts
        except Exception:
            import logging

            logging.getLogger(__name__).warning("冲突检测失败", exc_info=True)

    elif operation == "set_automation_enabled" and automation_id is not None:
        preview["automation_name"] = automation.name
        enabled = bool(args.get("enabled", True)) if args else True
        preview["target_enabled"] = enabled
        preview["summary"] = (
            f"{'启用' if enabled else '停用'}自动化规则：{automation.name}"
        )

    elif operation == "delete_automation" and automation_id is not None:
        preview["automation_name"] = automation.name
        preview["summary"] = f"删除自动化规则：{automation.name}"

    return RiskDecision(
        level=level,
        requires_approval=True,
        reasons=reasons,
        resource_version=resource_version,
        preview=preview,
    )


def classify_scene_execution(
    db: Session,
    context: AgentContext,
    scene_id: str,
) -> RiskDecision:
    scene = get_scene_or_404(db, context.household_id, scene_id)

    device_ids = {step.device_id for step in scene.steps}
    devices = list(
        db.scalars(
            select(Device).where(
                Device.household_id == context.household_id,
                Device.device_id.in_(device_ids),
            )
        )
    )

    devices_by_id = {device.device_id: device for device in devices}
    missing_device_ids = sorted(device_ids - devices_by_id.keys())
    high_risk_devices = [device for device in devices if _is_high_risk_device(device)]

    reasons: list[str] = []

    if missing_device_ids:
        level = RiskLevel.UNKNOWN
        reasons.append(f"无法确认以下设备的风险等级：{', '.join(missing_device_ids)}")
    elif scene.high_risk or high_risk_devices:
        level = RiskLevel.HIGH
        if scene.high_risk:
            reasons.append("场景被业务系统标记为高风险")
        if high_risk_devices:
            reasons.append(
                "包含高风险设备："
                + "、".join(device.name for device in high_risk_devices)
            )
    else:
        level = RiskLevel.LOW
        reasons.append("场景仅包含已识别的普通家居设备")

    requires_approval = (
        level in {RiskLevel.HIGH, RiskLevel.UNKNOWN}
        or not context.auto_execute_low_risk
    )
    # 高风险 / 未知风险始终需要审批，不受 confirm_high_risk 配置影响（§5.1）：
    # 安全策略不允许绕过高风险审批，confirm_high_risk 仅用于前端 UI 展示。
    # 低风险操作在 auto_execute_low_risk=True 时自动批准，否则仍需审批。

    return RiskDecision(
        level=level,
        requires_approval=requires_approval,
        reasons=reasons,
        resource_version=scene.updated_at.isoformat(),
        preview={
            "kind": "scene_execution",
            "scene_id": scene.id,
            "scene_name": scene.name,
            "enabled": scene.enabled,
            "risk_level": level.value,
            "device_count": len(device_ids),
            "summary": f"执行场景：{scene.name}",
            "steps": [
                {
                    "step_id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "device_id": step.device_id,
                    "device_name": (
                        devices_by_id[step.device_id].name
                        if step.device_id in devices_by_id
                        else None
                    ),
                    "order": step.step_order,
                }
                for step in sorted(scene.steps, key=lambda item: item.step_order)
            ],
        },
    )


def classify_device_operation(
    db: Session,
    context: AgentContext,
    operation: str,
    device_id: int,
    args: dict | None = None,
) -> RiskDecision:
    """分类设备控制操作的风险等级。

    Args:
        operation: 操作类型 (set_device_power / set_device_temperature / set_curtain_position)
        device_id: 设备数据库 ID
        args: 完整参数字典（用于构建丰富的预览信息）
    """
    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.household_id == context.household_id,
        )
    )
    reasons: list[str] = []

    if device is None:
        return RiskDecision(
            level=RiskLevel.UNKNOWN,
            requires_approval=True,
            reasons=["设备不存在或不属于当前家庭"],
            resource_version="",
            preview={
                "kind": operation,
                "operation": operation,
                "device_id": device_id,
                "risk_level": RiskLevel.UNKNOWN.value,
                "summary": "操作目标设备不存在",
            },
        )

    is_high_risk = _is_high_risk_device(device)

    if is_high_risk:
        level = RiskLevel.HIGH
        reasons.append(f"设备「{device.name}」属于高风险设备类型")
    else:
        level = RiskLevel.LOW
        reasons.append(f"设备「{device.name}」为普通家居设备")

    requires_approval = (
        level in {RiskLevel.HIGH, RiskLevel.UNKNOWN}
        or not context.auto_execute_low_risk
    )

    preview: dict = {
        "kind": operation,
        "operation": operation,
        "device_id": device_id,
        "device_name": device.name,
        "device_type": device.type,
        "risk_level": level.value,
    }

    if operation == "set_device_power" and args:
        power = args.get("power", "")
        preview["power"] = power
        preview["summary"] = f"{'打开' if power == 'on' else '关闭'}设备「{device.name}」"

    elif operation == "set_device_temperature" and args:
        temperature = args.get("temperature")
        mode = args.get("mode")
        preview["temperature"] = temperature
        preview["mode"] = mode
        preview["summary"] = f"设置空调「{device.name}」温度为 {temperature}°C"

    elif operation == "set_curtain_position" and args:
        position = args.get("position", 0)
        preview["position"] = position
        preview["summary"] = f"{'打开' if position > 0 else '关闭'}窗帘「{device.name}」至 {position}%"

    else:
        preview["summary"] = f"操作设备「{device.name}」"

    return RiskDecision(
        level=level,
        requires_approval=requires_approval,
        reasons=reasons,
        resource_version="",
        preview=preview,
    )
