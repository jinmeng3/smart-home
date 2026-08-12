from app.agents.context import AgentContext
from app.agents.errors import AgentToolExecutionError
from app.core.config import get_settings
from app.services.room import (
    get_room_by_household_service,
    list_rooms_by_household_service,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session


class ListRoomsInput(BaseModel):
    """列出房间的筛选参数。"""

    floor: str | None = Field(default=None, max_length=40)
    room_type: str | None = Field(default=None, max_length=32)


def list_rooms(db: Session, context: AgentContext, floor=None, room_type=None):
    """列出当前家庭的房间，可按楼层或房间类型筛选。返回列表，每项含 id、name、floor、room_type、area、comfort、device_count。"""
    return list_rooms_by_household_service(
        db,
        context.household_id,
        floor,
        room_type,
        get_settings().agent_tool_result_max_length,
    )


class GetRoomInput(BaseModel):
    """获取单个房间的参数。room_id 和 room_name 至少提供一个。"""

    room_id: int | None = None
    room_name: str | None = Field(default=None, max_length=80)


def get_room(db: Session, context: AgentContext, room_id=None, room_name=None):
    """获取指定房间详情及其设备列表。room_id 或 room_name 至少提供一个，优先按 room_id 查找。"""
    if room_id is None and not room_name:
        raise AgentToolExecutionError("room_id 或 room_name 至少提供一个")
    room = get_room_by_household_service(
        db, context.household_id, room_id=room_id, room_name=room_name
    )
    if room is None:
        raise AgentToolExecutionError("房间不存在")
    return room
