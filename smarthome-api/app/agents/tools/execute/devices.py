from datetime import datetime, timezone
from typing import Literal

from app.agents.context import AgentContext
from app.models.device import Device, DeviceLog, DeviceStatus
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class SetDevicePowerInput(BaseModel):
    """设置设备电源开关的参数。"""

    device_id: int = Field(gt=0, description="设备数据库ID")
    power: Literal["on", "off"]


def set_device_power(
    db: Session,
    context: AgentContext,
    device_id: int,
    power: str,
) -> dict:
    """设置设备电源开关（仅支持 light、air_conditioner、socket、curtain 类型）。"""
    try:
        device = db.scalar(
            select(Device).where(
                Device.id == device_id,
                Device.household_id == context.household_id,
            )
        )
        if device is None:
            return {
                "ok": False,
                "status": "failed",
                "device_name": None,
                "device_type": None,
                "power": power,
                "message": "设备不存在或不属于当前家庭",
            }

        if device.type not in {"light", "air_conditioner", "socket", "curtain"}:
            return {
                "ok": False,
                "status": "failed",
                "device_name": device.name,
                "device_type": device.type,
                "power": power,
                "message": f"设备类型「{device.type}」不支持电源控制",
            }

        now = datetime.now(timezone.utc)
        if power == "on":
            device.status = DeviceStatus.RUNNING
            action = "power_on"
            message = f"设备「{device.name}」已开机"
        else:
            device.status = DeviceStatus.ONLINE
            action = "power_off"
            message = f"设备「{device.name}」已关机"
        device.last_online = now
        device.updated_at = now
        db.add(
            DeviceLog(
                device_id=device.id,
                action=action,
                message=message,
            )
        )
        db.commit()
        return {
            "ok": True,
            "status": device.status.value,
            "device_name": device.name,
            "device_type": device.type,
            "power": power,
            "message": message,
        }
    except Exception:  # noqa: BLE001
        db.rollback()
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": "设置设备电源失败，请稍后重试",
        }


class SetDeviceTemperatureInput(BaseModel):
    """设置空调温度的参数。"""

    device_id: int = Field(gt=0, description="设备数据库ID")
    temperature: float = Field(ge=16, le=30, description="目标温度（摄氏度）")
    mode: Literal["cool", "heat", "fan", "auto"] | None = Field(
        default=None, description="空调模式"
    )
    fan_speed: Literal["low", "medium", "high", "auto"] | None = Field(
        default=None, description="风扇速度"
    )


def set_device_temperature(
    db: Session,
    context: AgentContext,
    device_id: int,
    temperature: float,
    mode: str | None = None,
    fan_speed: str | None = None,
) -> dict:
    """设置空调目标温度，仅支持 air_conditioner 类型设备。"""
    try:
        device = db.scalar(
            select(Device).where(
                Device.id == device_id,
                Device.household_id == context.household_id,
            )
        )
        if device is None:
            return {
                "ok": False,
                "status": "failed",
                "device_name": None,
                "temperature": temperature,
                "mode": mode,
                "fan_speed": fan_speed,
                "message": "设备不存在或不属于当前家庭",
            }

        if device.type != "air_conditioner":
            return {
                "ok": False,
                "status": "failed",
                "device_name": device.name,
                "temperature": temperature,
                "mode": mode,
                "fan_speed": fan_speed,
                "message": f"设备类型「{device.type}」不支持温度设置",
            }

        now = datetime.now(timezone.utc)
        device.status = DeviceStatus.RUNNING
        device.last_online = now
        device.updated_at = now

        parts = [f"空调「{device.name}」温度设置为 {temperature:.1f}℃"]
        if mode is not None:
            mode_labels = {"cool": "制冷", "heat": "制热", "fan": "送风", "auto": "自动"}
            parts.append(f"模式：{mode_labels.get(mode, mode)}")
        if fan_speed is not None:
            speed_labels = {"low": "低风", "medium": "中风", "high": "高风", "auto": "自动"}
            parts.append(f"风速：{speed_labels.get(fan_speed, fan_speed)}")
        message = "，".join(parts)

        db.add(
            DeviceLog(
                device_id=device.id,
                action="set_temperature",
                message=message,
            )
        )
        db.commit()
        return {
            "ok": True,
            "status": device.status.value,
            "device_name": device.name,
            "temperature": temperature,
            "mode": mode,
            "fan_speed": fan_speed,
            "message": message,
        }
    except Exception:  # noqa: BLE001
        db.rollback()
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": "设置空调温度失败，请稍后重试",
        }


class SetCurtainPositionInput(BaseModel):
    """设置窗帘开合度的参数。"""

    device_id: int = Field(gt=0, description="设备数据库ID")
    position: int = Field(ge=0, le=100, description="0=完全关闭，100=完全打开")


def set_curtain_position(
    db: Session,
    context: AgentContext,
    device_id: int,
    position: int,
) -> dict:
    """设置窗帘开合度，仅支持 curtain 类型设备。"""
    try:
        device = db.scalar(
            select(Device).where(
                Device.id == device_id,
                Device.household_id == context.household_id,
            )
        )
        if device is None:
            return {
                "ok": False,
                "status": "failed",
                "device_name": None,
                "position": position,
                "message": "设备不存在或不属于当前家庭",
            }

        if device.type != "curtain":
            return {
                "ok": False,
                "status": "failed",
                "device_name": device.name,
                "position": position,
                "message": f"设备类型「{device.type}」不支持窗帘控制",
            }

        now = datetime.now(timezone.utc)
        if position > 0:
            device.status = DeviceStatus.RUNNING
            action = "curtain_open"
        else:
            device.status = DeviceStatus.ONLINE
            action = "curtain_close"
        device.last_online = now
        device.updated_at = now
        message = f"窗帘「{device.name}」开合度设置为 {position}%"
        db.add(
            DeviceLog(
                device_id=device.id,
                action=action,
                message=message,
            )
        )
        db.commit()
        return {
            "ok": True,
            "status": device.status.value,
            "device_name": device.name,
            "position": position,
            "message": message,
        }
    except Exception:  # noqa: BLE001
        db.rollback()
        return {
            "ok": False,
            "status": "failed",
            "code": "AGENT_EXECUTION_ERROR",
            "error": "设置窗帘位置失败，请稍后重试",
        }