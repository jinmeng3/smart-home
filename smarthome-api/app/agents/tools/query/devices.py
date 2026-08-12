from app.agents.context import AgentContext
from app.models.device import Device, DeviceStatus
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session


class ListDevicesInput(BaseModel):
    room: str | None = Field(default=None, max_length=80)
    device_type: str | None = Field(default=None, max_length=80)
    status: str | None = None


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
