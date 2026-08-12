from app.agents.context import AgentContext
from app.agents.errors import AgentToolExecutionError
from app.core.config import get_settings
from app.services.device import (
    get_device_by_household_service,
    list_devices_by_household_service,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class ListDevicesInput(BaseModel):
    """列出设备的筛选参数。"""

    room: str | None = Field(default=None, max_length=80)
    device_type: str | None = Field(default=None, max_length=32)
    status: str | None = None


def list_devices(
    db: Session, context: AgentContext, room=None, device_type=None, status=None
):
    """列出当前家庭的设备，可按房间名称、设备类型、状态筛选。返回列表含设备 id、名称、类型、状态、房间名等。"""
    return list_devices_by_household_service(
        db,
        context.household_id,
        room,
        device_type,
        status,
        get_settings().agent_tool_result_max_length,
    )


class GetDeviceInput(BaseModel):
    """获取单个设备的参数。device_id 和 name 至少提供一个。"""

    device_id: int | None = None
    name: str | None = Field(default=None, max_length=80)


def get_device(db: Session, context: AgentContext, device_id=None, name=None):
    """获取指定设备详情（状态、连接方式、固件、最后在线时间等）。device_id 或 name 至少提供一个。"""
    if device_id is None and not name:
        raise AgentToolExecutionError("device_id 或 name 至少提供一个")
    result = get_device_by_household_service(
        db, context.household_id, device_id=device_id, name=name
    )
    if result is None:
        raise AgentToolExecutionError("设备不存在")
    return result
