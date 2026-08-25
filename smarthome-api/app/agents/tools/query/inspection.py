from app.agents.context import AgentContext
from app.models.automation import Automation
from app.models.device import Device, DeviceStatus
from app.models.scene import Scene
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session


class InspectHouseholdHealthInput(BaseModel):
    """全屋巡检参数（无筛选条件，默认聚合当前家庭全部状态）。"""


def inspect_household_health(db: Session, context: AgentContext):
    """全屋健康巡检：汇总设备、场景、自动化规则的状态，给出整体健康评级。"""
    try:
        household_id = context.household_id

        # --- Device ---
        devices = db.scalars(
            select(Device).where(Device.household_id == household_id)
        ).all()

        total = len(devices)
        online = sum(1 for d in devices if d.status == DeviceStatus.ONLINE)
        offline = sum(1 for d in devices if d.status == DeviceStatus.OFFLINE)
        warning = sum(1 for d in devices if d.status == DeviceStatus.WARNING)
        running = sum(1 for d in devices if d.status == DeviceStatus.RUNNING)

        offline_devices = [
            {
                "id": d.id,
                "name": d.name,
                "room": d.room,
                "type": d.type,
                "last_online": d.last_online.isoformat() if d.last_online else None,
            }
            for d in devices
            if d.status == DeviceStatus.OFFLINE
        ]

        warning_devices = [
            {
                "id": d.id,
                "name": d.name,
                "room": d.room,
                "type": d.type,
            }
            for d in devices
            if d.status == DeviceStatus.WARNING
        ]

        # --- Scene ---
        scenes = db.scalars(
            select(Scene).where(Scene.household_id == household_id)
        ).all()
        scene_total = len(scenes)
        scene_enabled = sum(1 for s in scenes if s.enabled)
        scene_disabled = scene_total - scene_enabled
        scene_high_risk = sum(1 for s in scenes if s.high_risk)

        # --- Automation ---
        automations = db.scalars(
            select(Automation).where(Automation.household_id == household_id)
        ).all()
        automation_total = len(automations)
        automation_enabled = sum(1 for a in automations if a.enabled)
        automation_disabled = automation_total - automation_enabled

        # --- Overall health ---
        if warning > 0:
            overall_health = "critical"
        elif offline > 0:
            overall_health = "warning"
        else:
            overall_health = "good"

        return {
            "device_summary": {
                "total": total,
                "online": online,
                "offline": offline,
                "warning": warning,
                "running": running,
            },
            "offline_devices": offline_devices,
            "warning_devices": warning_devices,
            "scene_summary": {
                "total": scene_total,
                "enabled": scene_enabled,
                "disabled": scene_disabled,
                "high_risk": scene_high_risk,
            },
            "automation_summary": {
                "total": automation_total,
                "enabled": automation_enabled,
                "disabled": automation_disabled,
            },
            "overall_health": overall_health,
        }
    except Exception as e:  # noqa: BLE001
        return {"ok": False, "error": str(e)}