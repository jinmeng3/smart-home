import json
from datetime import date
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import CURRENT_USER_DEPENDENCY, DB_DEPENDENCY
from app.models.membership import HouseholdMembership
from app.models.room import Room, RoomDevice, RoomEnvironmentReport
from app.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.room import (
    EnvironmentLatestRead,
    EnvironmentReportRead,
    EnvironmentTrendRead,
    RoomDeviceListRead,
    RoomDeviceMetaWrite,
    RoomDevicesWrite,
    RoomDeviceWrite,
    RoomListRead,
    RoomLogListRead,
    RoomQuickActionWrite,
    RoomRead,
    RoomSceneExecuteWrite,
    RoomWrite,
)
from app.schemas.scene import SceneExecutionRead, SceneListRead, ScenePreviewRead
from app.services.room import (
    environment_trends,
    latest_environment,
    list_room_devices,
    list_room_logs,
    replace_room_devices,
    save_room,
    write_activity,
)
from app.services.scene import execute_scene, list_scenes, preview_scene

router = APIRouter(prefix="/rooms", tags=["rooms"])
environment_router = APIRouter(prefix="/environment", tags=["rooms"])


def serialize(room: Room) -> RoomRead:
    return RoomRead(
        id=room.id,
        name=room.name,
        floor=room.floor,
        room_type=room.room_type,
        image_url=room.image_url,
        area=room.area,
        comfort=room.comfort,
        icon=room.icon,
        theme_color=room.theme_color,
        version=room.version,
        temperature=room.temperature,
        humidity=room.humidity,
        pm25=room.pm25,
        illuminance=room.illuminance,
        noise=room.noise,
        device_count=room.device_count,
        online_count=room.online_count,
        device_states=json.loads(room.device_states),
        updated_at=room.updated_at,
    )


def accessible_rooms(db: Session, user: User):
    household_ids = select(HouseholdMembership.household_id).where(
        HouseholdMembership.user_id == user.id
    )
    return select(Room).where(Room.household_id.in_(household_ids))


@router.get("", response_model=ApiResponse[RoomListRead])
def list_rooms(
    floor: str | None = Query(default=None),
    room_type: str | None = Query(default=None),
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomListRead]:
    query = accessible_rooms(db, current_user).order_by(Room.id)
    if floor:
        query = query.where(Room.floor == floor)
    if room_type:
        query = query.where(Room.room_type == room_type)
    rooms = list(db.scalars(query))
    return ApiResponse.ok(
        RoomListRead(items=[serialize(room) for room in rooms], total=len(rooms))
    )


def get_room(db: Session, user: User, room_id: int) -> Room:
    room = db.scalar(accessible_rooms(db, user).where(Room.id == room_id))
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room


def default_household_id(db: Session, user: User) -> int:
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(status_code=403, detail="当前用户尚未加入家庭")
    return household_id


@router.post(
    "", response_model=ApiResponse[RoomRead], status_code=status.HTTP_201_CREATED
)
def add_room(
    payload: RoomWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    room = save_room(db, default_household_id(db, current_user), payload)
    return ApiResponse.ok(serialize(room), "created")


@router.put("/{room_id}", response_model=ApiResponse[RoomRead])
def edit_room(
    room_id: int,
    payload: RoomWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    room = get_room(db, current_user, room_id)
    return ApiResponse.ok(serialize(save_room(db, room.household_id, payload, room)))


@router.get("/{room_id}/logs", response_model=ApiResponse[RoomLogListRead])
def get_room_logs(
    room_id: int,
    date_from: date | None = None,
    date_to: date | None = None,
    keyword: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomLogListRead]:
    return ApiResponse.ok(
        list_room_logs(
            db,
            get_room(db, current_user, room_id),
            page,
            page_size,
            keyword,
            date_from,
            date_to,
        )
    )


@router.get("/{room_id}/devices", response_model=ApiResponse[RoomDeviceListRead])
def get_room_devices(
    room_id: int,
    keyword: str | None = None,
    type: str | None = None,
    status: str | None = None,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDeviceListRead]:
    return ApiResponse.ok(
        list_room_devices(
            db, get_room(db, current_user, room_id), keyword, type, status
        )
    )


@router.put("/{room_id}/devices", response_model=ApiResponse[RoomDeviceListRead])
def set_room_devices(
    room_id: int,
    payload: RoomDevicesWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDeviceListRead]:
    return ApiResponse.ok(
        replace_room_devices(db, get_room(db, current_user, room_id), payload)
    )


@router.patch(
    "/{room_id}/devices/{device_id}", response_model=ApiResponse[RoomDeviceListRead]
)
def edit_room_device(
    room_id: int,
    device_id: int,
    payload: RoomDeviceMetaWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomDeviceListRead]:
    room = get_room(db, current_user, room_id)
    binding = db.scalar(
        select(RoomDevice).where(
            RoomDevice.room_id == room.id, RoomDevice.device_id == device_id
        )
    )
    if not binding:
        raise HTTPException(status_code=404, detail="房间设备不存在")
    changes = payload.model_dump(exclude_unset=True)
    if "group" in changes:
        changes["group_name"] = changes.pop("group")
    for field, value in changes.items():
        setattr(binding, field, value)
    db.commit()
    return ApiResponse.ok(list_room_devices(db, room))


@router.get(
    "/{room_id}/environment/latest", response_model=ApiResponse[EnvironmentLatestRead]
)
def get_environment_latest(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[EnvironmentLatestRead]:
    return ApiResponse.ok(latest_environment(db, get_room(db, current_user, room_id)))


@router.get(
    "/{room_id}/environment/trends", response_model=ApiResponse[EnvironmentTrendRead]
)
def get_environment_trends(
    room_id: int,
    metrics: str = "temperature,humidity",
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[EnvironmentTrendRead]:
    return ApiResponse.ok(
        environment_trends(
            db,
            get_room(db, current_user, room_id),
            [item.strip() for item in metrics.split(",") if item.strip()],
        )
    )


@router.get("/{room_id}/scenes", response_model=ApiResponse[SceneListRead])
def get_room_scenes(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneListRead]:
    room = get_room(db, current_user, room_id)
    scenes = list_scenes(db, room.name, None, "all")
    return ApiResponse.ok(scenes)


@router.post(
    "/{room_id}/scenes/{scene_id}/preview", response_model=ApiResponse[ScenePreviewRead]
)
def preview_room_scene(
    room_id: int,
    scene_id: str,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[ScenePreviewRead]:
    get_room(db, current_user, room_id)
    return ApiResponse.ok(preview_scene(db, scene_id))


@router.post(
    "/{room_id}/scenes/{scene_id}/execute",
    response_model=ApiResponse[SceneExecutionRead],
)
def execute_room_scene(
    room_id: int,
    scene_id: str,
    payload: RoomSceneExecuteWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[SceneExecutionRead]:
    room = get_room(db, current_user, room_id)
    result = execute_scene(db, scene_id, False, "room")
    write_activity(db, room, f"执行场景：{scene_id}", "scene")
    db.commit()
    return ApiResponse.ok(result)


@router.post(
    "/{room_id}/environment/reports",
    response_model=ApiResponse[EnvironmentReportRead],
    status_code=status.HTTP_202_ACCEPTED,
)
def create_environment_report(
    room_id: int,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[EnvironmentReportRead]:
    room = get_room(db, current_user, room_id)
    report = RoomEnvironmentReport(id=f"report-{uuid4().hex}", room_id=room.id)
    db.add(report)
    db.commit()
    return ApiResponse.ok(
        EnvironmentReportRead(task_id=report.id, status=report.status)
    )


@environment_router.get(
    "/reports/{task_id}", response_model=ApiResponse[EnvironmentReportRead]
)
def get_environment_report(
    task_id: str,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[EnvironmentReportRead]:
    accessible = accessible_rooms(db, current_user).subquery()
    report = db.scalar(
        select(RoomEnvironmentReport).where(
            RoomEnvironmentReport.id == task_id,
            RoomEnvironmentReport.room_id.in_(select(accessible.c.id)),
        )
    )
    if not report:
        raise HTTPException(status_code=404, detail="环境报告任务不存在")
    return ApiResponse.ok(
        EnvironmentReportRead(
            task_id=report.id, status=report.status, download_url=report.download_url
        )
    )


@router.patch("/{room_id}/device", response_model=ApiResponse[RoomRead])
def update_device(
    room_id: int,
    payload: RoomDeviceWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    room = get_room(db, current_user, room_id)
    states = json.loads(room.device_states)
    states[payload.device] = payload.value
    room.device_states = json.dumps(states, ensure_ascii=False)
    write_activity(db, room, f"{payload.device} 状态更新")
    db.commit()
    db.refresh(room)
    return ApiResponse.ok(serialize(room), "设备状态已更新")


@router.post("/{room_id}/quick-action", response_model=ApiResponse[RoomRead])
def quick_action(
    room_id: int,
    payload: RoomQuickActionWrite,
    db: Session = DB_DEPENDENCY,
    current_user: User = CURRENT_USER_DEPENDENCY,
) -> ApiResponse[RoomRead]:
    room = get_room(db, current_user, room_id)
    states = json.loads(room.device_states)
    key_map = {
        "all_lights": "light",
        "air_conditioner": "airConditioner",
        "curtains": "curtain",
    }
    states[key_map[payload.action]] = payload.action != "air_conditioner"
    room.device_states = json.dumps(states, ensure_ascii=False)
    write_activity(db, room, f"快捷操作：{payload.action}")
    db.commit()
    db.refresh(room)
    return ApiResponse.ok(serialize(room), "快捷操作已执行")
