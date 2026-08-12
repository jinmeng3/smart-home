from app.agents.context import AgentContext
from app.models.device import Device, DeviceLog, DeviceStatus
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class ListDevicesInput(BaseModel):
    room: str | None = Field(default=None, max_length=80)
    device_type: str | None = Field(default=None, max_length=32)
    status: str | None = None


class GetDeviceInput(BaseModel):
    device_id: int = Field(gt=0)


def _list_devices(
    db: Session, context: AgentContext, room=None, device_type=None, status=None
):
    query = select(Device).where(Device.household_id == context.household_id)
    if room:
        query = query.where(Device.room == room)
    if device_type:
        query = query.where(Device.type == device_type)
    if status:
        query = query.where(Device.status == status)

    rows = db.scalars(query.limit(50)).all()

    return [
        {
            "id": d.id,
            "name": d.name,
            "room": d.room,
            "type": d.type,
            "status": d.status.value
            if isinstance(d.status, DeviceStatus)
            else d.status,
            "brand": d.brand,
        }
        for d in rows
    ]


def _get_device(db: Session, context: AgentContext, device_id: int):
    device = db.scalar(
        select(Device).where(
            Device.id == device_id,
            Device.household_id == context.household_id,
        )
    )
    if device is None:
        return {"found": False, "device_id": device_id}

    logs = db.scalars(
        select(DeviceLog)
        .where(DeviceLog.device_id == device.id)
        .order_by(DeviceLog.created_at.desc())
        .limit(20)
    ).all()
    return {
        "found": True,
        "id": device.id,
        "name": device.name,
        "room": device.room,
        "type": device.type,
        "brand": device.brand,
        "status": device.status.value
        if isinstance(device.status, DeviceStatus)
        else device.status,
        "connection": device.connection,
        "firmware": device.firmware,
        "last_online": device.last_online,
        "logs": [
            {
                "action": log.action,
                "message": log.message,
                "created_at": log.created_at,
            }
            for log in logs
        ],
    }
