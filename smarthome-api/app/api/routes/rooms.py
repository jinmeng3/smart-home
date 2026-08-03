import json

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.membership import HouseholdMembership
from app.models.room import Room
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.room import RoomDeviceWrite, RoomListRead, RoomQuickActionWrite, RoomRead

router = APIRouter(prefix="/rooms", tags=["rooms"])


def serialize(room: Room) -> RoomRead:
    return RoomRead(
        id=room.id, name=room.name, floor=room.floor, room_type=room.room_type,
        image_url=room.image_url, area=room.area, comfort=room.comfort,
        temperature=room.temperature, humidity=room.humidity, pm25=room.pm25,
        illuminance=room.illuminance, noise=room.noise, device_count=room.device_count,
        online_count=room.online_count, device_states=json.loads(room.device_states),
        updated_at=room.updated_at,
    )


def accessible_rooms(db: Session, user: User):
    household_ids = select(HouseholdMembership.household_id).where(HouseholdMembership.user_id == user.id)
    return select(Room).where(Room.household_id.in_(household_ids))


@router.get("", response_model=ApiResponse[RoomListRead])
def list_rooms(
    floor: str | None = Query(default=None), room_type: str | None = Query(default=None),
    db: Session = DB_DEPENDENCY, current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomListRead]:
    query = accessible_rooms(db, current_user).order_by(Room.id)
    if floor:
        query = query.where(Room.floor == floor)
    if room_type:
        query = query.where(Room.room_type == room_type)
    rooms = list(db.scalars(query))
    return ApiResponse.ok(RoomListRead(items=[serialize(room) for room in rooms], total=len(rooms)))


def get_room(db: Session, user: User, room_id: int) -> Room:
    room = db.scalar(accessible_rooms(db, user).where(Room.id == room_id))
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room


@router.patch("/{room_id}/device", response_model=ApiResponse[RoomRead])
def update_device(room_id: int, payload: RoomDeviceWrite, db: Session = DB_DEPENDENCY, current_user: User = CURRENT_USER_DEPENDENCY) -> ApiResponse[RoomRead]:
    room = get_room(db, current_user, room_id)
    states = json.loads(room.device_states)
    states[payload.device] = payload.value
    room.device_states = json.dumps(states, ensure_ascii=False)
    db.commit()
    db.refresh(room)
    return ApiResponse.ok(serialize(room), "设备状态已更新")


@router.post("/{room_id}/quick-action", response_model=ApiResponse[RoomRead])
def quick_action(room_id: int, payload: RoomQuickActionWrite, db: Session = DB_DEPENDENCY, current_user: User = CURRENT_USER_DEPENDENCY) -> ApiResponse[RoomRead]:
    room = get_room(db, current_user, room_id)
    states = json.loads(room.device_states)
    key_map = {"all_lights": "light", "air_conditioner": "airConditioner", "curtains": "curtain"}
    states[key_map[payload.action]] = payload.action != "air_conditioner"
    room.device_states = json.dumps(states, ensure_ascii=False)
    db.commit()
    db.refresh(room)
    return ApiResponse.ok(serialize(room), "快捷操作已执行")
