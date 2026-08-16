from app.agents.context import AgentContext
from app.agents.risk.policy import RiskDecision, RiskLevel
from app.models.device import Device
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
) -> RiskDecision:
    """分类自动化操作的风险等级。

    Args:
        operation: 操作类型 (create_automation / update_automation / set_automation_enabled / delete_automation)
        automation_id: 自动化规则 ID（创建时可为 None）
        actions: 动作列表（仅创建/更新时需要）
    """
    reasons: list[str] = []
    resource_version = ""

    # 对已有资源的所有配置操作保存版本快照，批准后必须再次校验。
    if automation_id is not None:
        from app.services.automation import get_automation as get_automation_svc

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
            a.get("device_id") for a in (actions or []) if a.get("device_id") is not None
        }
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

        if missing_device_ids:
            level = RiskLevel.UNKNOWN
            reasons.append("动作包含不存在或不属于当前家庭的设备")
        elif high_risk_devices:
            level = RiskLevel.HIGH
            reasons.append(
                "包含高风险设备：" + "、".join(d.name for d in high_risk_devices)
            )
        else:
            level = RiskLevel.LOW
            reasons.append("仅包含已识别的普通家居设备操作")

    else:
        level = RiskLevel.UNKNOWN
        reasons.append(f"未知的自动化操作类型：{operation}")

    # 自动化创建、修改、启停和删除均属于配置变更，必须人工确认。
    return RiskDecision(
        level=level,
        requires_approval=True,
        reasons=reasons,
        resource_version=resource_version,
        preview={
            "operation": operation,
            "automation_id": automation_id,
            "risk_level": level,
        },
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

    return RiskDecision(
        level=level,
        requires_approval=requires_approval,
        reasons=reasons,
        resource_version=scene.updated_at.isoformat(),
        preview={
            "scene_id": scene.id,
            "scene_name": scene.name,
            "enabled": scene.enabled,
            "risk_level": level,
            "device_count": len(device_ids),
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
