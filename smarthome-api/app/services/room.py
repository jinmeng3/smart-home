import json
from datetime import date, datetime, time, timezone

from fastapi import HTTPException, status
from sqlalchemy import delete, func, insert, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.device import Device, DeviceStatus
from app.models.membership import HouseholdMembership
from app.models.room import (
    Room,
    RoomActivityLog,
    RoomDevice,
)
from app.models.user import User
from app.schemas.room import (
    RoomDetailRead,
    RoomDeviceListItem,
    RoomDeviceListRead,
    RoomDeviceMetaWrite,
    RoomDevicesWrite,
    RoomDeviceWrite,
    RoomInput,
    RoomListRead,
    RoomLogListRead,
    RoomLogRead,
    RoomQuickActionWrite,
    RoomRead,
    RoomSceneExecuteWrite,
    RoomStatsRead,
)
from app.schemas.scene import SceneExecutionRead, SceneListRead, ScenePreviewRead
from app.services.scene import (
    get_scene_preview_service,
    get_scenes_service,
    run_scene_service,
)


def accessible_rooms(db: Session, user: User):
    """构建当前用户所有可访问房间的查询。"""
    household_ids = select(HouseholdMembership.household_id).where(
        HouseholdMembership.user_id == user.id
    )
    return select(Room).where(Room.household_id.in_(household_ids))


def get_room_or_404(db: Session, user: User, room_id: int) -> Room:
    """按ID获取用户可访问的房间，不存在时抛出404。"""
    room = db.scalar(accessible_rooms(db, user).where(Room.id == room_id))
    if not room:
        raise HTTPException(status_code=404, detail="房间不存在")
    return room


def _load_room_devices(db: Session, room_read: RoomRead, room_id: int) -> RoomRead:
    """从数据库加载房间设备列表并填充到 RoomRead.device。"""
    rows = db.execute(
        select(RoomDevice, Device)
        .join(Device)
        .where(RoomDevice.room_id == room_id)
        .order_by(RoomDevice.sort_order, Device.id)
    ).all()
    room_read.device = [
        RoomDeviceListItem(
            id=device.id,
            name=device.name,
            type=device.type,
            brand=device.brand,
            status=device.status,
            icon=device.icon,
            color=device.color,
            group=binding.group_name,
            favorite=binding.favorite,
            sort_order=binding.sort_order,
            updated_at=device.updated_at,
        )
        for binding, device in rows
    ]
    return room_read


def default_household_id(db: Session, user: User) -> int:
    """获取用户默认家庭ID，未加入家庭时抛出403。"""
    household_id = db.scalar(
        select(HouseholdMembership.household_id)
        .where(HouseholdMembership.user_id == user.id)
        .order_by(HouseholdMembership.id)
    )
    if household_id is None:
        raise HTTPException(status_code=403, detail="当前用户尚未加入家庭")
    return household_id


# === 房间 CRUD ===


def list_rooms_service(
    db: Session,
    user: User,
    floor: str | None = None,
    room_type: str | None = None,
) -> RoomListRead:
    """按楼层和类型筛选房间列表。"""
    query = accessible_rooms(db, user).order_by(Room.id)
    if floor:
        query = query.where(Room.floor == floor)
    if room_type:
        query = query.where(Room.room_type == room_type)
    rooms = list(db.scalars(query))
    if rooms:
        rows = db.execute(
            select(RoomDevice, Device)
            .join(Device)
            .where(RoomDevice.room_id.in_([room.id for room in rooms]))
            .order_by(RoomDevice.sort_order, Device.id)
        ).all()
    devices_by_room: dict[int, list[RoomDeviceListItem]] = {}
    for binding, device in rows:
        devices_by_room.setdefault(binding.room_id, []).append(
            RoomDeviceListItem(
                id=device.id,
                name=device.name,
                type=device.type,
                brand=device.brand,
                status=device.status,
                icon=device.icon,
                color=device.color,
                group=binding.group_name,
                favorite=binding.favorite,
                sort_order=binding.sort_order,
                updated_at=device.updated_at,
            )
        )
    items = []
    for room in rooms:
        room_read = RoomRead.model_validate(room)
        room_devices = devices_by_room.get(room.id, [])
        room_read.device = room_devices
        room_read.device_count = len(room_devices)
        room_read.online_count = sum(
            d.status in {"online", "running"} for d in room_devices
        )
        items.append(room_read)
    return RoomListRead(items=items, total=len(items))


def list_room_stats_service(db: Session, user: User) -> RoomStatsRead:
    """获取当前用户所有房间的统计概览。"""
    rooms = list(db.scalars(accessible_rooms(db, user).order_by(Room.id)))
    total = len(rooms)
    if not rooms:
        return RoomStatsRead(
            room_count=0,
            room_count_change=0,
            online_rate=0.0,
            alert_count=0,
            pending_alert_count=0,
        )
    rows = db.execute(
        select(RoomDevice, Device)
        .join(Device)
        .where(RoomDevice.room_id.in_([room.id for room in rooms]))
    ).all()
    total_devices = len(rows)
    online_count = sum(device.status in {"online", "running"} for _, device in rows)
    online_rate = (online_count / total_devices * 100) if total_devices > 0 else 0.0

    return RoomStatsRead(
        room_count=total,
        room_count_change=0,
        online_rate=round(online_rate, 1),
        alert_count=total - 1 if total > 0 else 0,
        pending_alert_count=total - 1 if total > 0 else 0,
    )


def add_room_service(db: Session, user: User, payload: RoomInput) -> RoomRead:
    """创建房间。"""
    household_id = default_household_id(db, user)
    room = Room(household_id=household_id, **payload.model_dump(exclude={"device_ids"}))
    db.add(room)
    try:
        db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="房间名已存在")

    for device_id in payload.device_ids:
        device = db.scalar(select(Device).where(Device.id == device_id))
        if device:
            db.add(RoomDevice(room_id=room.id, device_id=device.id))

    db.commit()
    db.refresh(room)
    return _load_room_devices(db, RoomRead.model_validate(room), room.id)


def edit_room_service(
    db: Session, user: User, room_id: int, payload: RoomInput
) -> RoomRead:
    """更新房间信息。"""
    room = get_room_or_404(db, user, room_id)
    for key, value in payload.model_dump(exclude={"device_ids"}).items():
        setattr(room, key, value)

    existing_ids = set(
        db.scalars(
            select(RoomDevice.device_id).where(RoomDevice.room_id == room_id)
        ).all()
    )
    new_ids = set(payload.device_ids)

    to_delete = existing_ids - new_ids
    to_add = new_ids - existing_ids

    if to_delete:
        db.execute(
            delete(RoomDevice).where(
                RoomDevice.room_id == room_id,
                RoomDevice.device_id.in_(to_delete),
            )
        )
    if to_add:
        db.execute(
            insert(RoomDevice).values(
                [{"room_id": room_id, "device_id": did} for did in to_add]
            )
        )
    if new_ids:
        devices = db.scalars(select(Device).where(Device.id.in_(new_ids))).all()
        room.device_count = len(devices)
        room.online_count = sum(d.status in {"online", "running"} for d in devices)
    else:
        room.device_count = 0
        room.online_count = 0
    db.commit()
    db.refresh(room)
    return _load_room_devices(db, RoomRead.model_validate(room), room.id)


def get_room_detail_service(db: Session, user: User, room_id: int) -> RoomDetailRead:
    """获取房间详情。"""
    room = get_room_or_404(db, user, room_id)
    recent_log = db.scalar(
        select(RoomActivityLog)
        .where(RoomActivityLog.room_id == room.id)
        .order_by(RoomActivityLog.occurred_at.desc())
    )
    recent_activity = None
    recent_activity_time = None
    if recent_log:
        recent_activity = recent_log.event
        now = datetime.now(timezone.utc)
        diff = now - recent_log.occurred_at
        minutes = int(diff.total_seconds() / 60)
        if minutes < 1:
            recent_activity_time = "刚刚"
        elif minutes < 60:
            recent_activity_time = f"{minutes} 分钟前"
        elif minutes < 1440:
            recent_activity_time = f"{minutes // 60} 小时前"
        else:
            recent_activity_time = f"{minutes // 1440} 天前"

    room_read = RoomRead.model_validate(room)

    return RoomDetailRead(
        room=room_read,
        current_scene="休闲模式",  # 暂用默认值，后续可从场景接口获取
        recent_activity=recent_activity,
        recent_activity_time=recent_activity_time,
    )


def delete_room_service(db: Session, user: User, room_id: int):
    room = get_room_or_404(db, user, room_id)
    db.delete(room)
    db.commit()


# === 房间日志 ===


def write_activity(
    db: Session,
    room: Room,
    event: str,
    source: str = "manual",
    device_id: int | None = None,
) -> None:
    db.add(
        RoomActivityLog(
            room_id=room.id,
            device_id=device_id,
            source=source,
            event=event,
            tags_json=json.dumps([room.name], ensure_ascii=False),
        )
    )


def list_room_logs(
    db: Session,
    room: Room,
    page: int,
    page_size: int,
    keyword: str | None,
    date_from: date | None,
    date_to: date | None,
) -> RoomLogListRead:
    filters = [RoomActivityLog.room_id == room.id]
    if keyword:
        filters.append(RoomActivityLog.event.like(f"%{keyword.strip()}%"))
    if date_from:
        filters.append(
            RoomActivityLog.occurred_at
            >= datetime.combine(date_from, time.min, tzinfo=timezone.utc)
        )
    if date_to:
        filters.append(
            RoomActivityLog.occurred_at
            <= datetime.combine(date_to, time.max, tzinfo=timezone.utc)
        )
    total = (
        db.scalar(select(func.count()).select_from(RoomActivityLog).where(*filters))
        or 0
    )
    rows = db.execute(
        select(RoomActivityLog, Device.name)
        .outerjoin(Device, Device.id == RoomActivityLog.device_id)
        .where(*filters)
        .order_by(RoomActivityLog.occurred_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return RoomLogListRead(
        total=total,
        items=[
            RoomLogRead(
                id=log.id,
                occurred_at=log.occurred_at,
                source=log.source,
                event=log.event,
                result=log.result,
                duration_ms=log.duration_ms,
                device_id=log.device_id,
                device_name=name,
                tags=json.loads(log.tags_json),
                detail=json.loads(log.detail_json),
            )
            for log, name in rows
        ],
    )


def get_room_logs_service(
    db: Session,
    user: User,
    room_id: int,
    page: int,
    page_size: int,
    keyword: str | None,
    date_from: date | None,
    date_to: date | None,
) -> RoomLogListRead:
    """分页查询房间操作日志。"""
    room = get_room_or_404(db, user, room_id)
    return list_room_logs(db, room, page, page_size, keyword, date_from, date_to)


# === 房间设备 ===


def replace_room_devices(
    db: Session, room: Room, payload: RoomDevicesWrite
) -> RoomDeviceListRead:
    ids = [item.device_id for item in payload.devices]
    devices = {
        item.id: item
        for item in db.scalars(select(Device).where(Device.id.in_(ids))).all()
    }
    if set(ids) != devices.keys():
        raise HTTPException(status_code=422, detail="部分设备不存在")
    db.query(RoomDevice).filter(RoomDevice.room_id == room.id).delete(
        synchronize_session=False
    )
    for item in payload.devices:
        devices[item.device_id].room = room.name
        db.add(
            RoomDevice(
                room_id=room.id,
                device_id=item.device_id,
                group_name=item.group,
                favorite=item.favorite,
                sort_order=item.sort_order,
            )
        )
    room.device_count = len(ids)
    room.online_count = sum(
        devices[item].status in {"online", "running"} for item in ids
    )
    db.commit()
    return list_room_devices(db, room)


def list_room_devices(
    db: Session,
    room: Room,
    keyword: str | None = None,
    device_type: str | None = None,
    device_status: str | None = None,
) -> RoomDeviceListRead:
    filters = [RoomDevice.room_id == room.id]
    if keyword:
        filters.append(
            or_(
                Device.name.like(f"%{keyword.strip()}%"),
                Device.brand.like(f"%{keyword.strip()}%"),
            )
        )
    if device_type:
        filters.append(Device.type == device_type)
    if device_status:
        filters.append(Device.status == device_status)
    rows = db.execute(
        select(RoomDevice, Device)
        .join(Device)
        .where(*filters)
        .order_by(RoomDevice.sort_order, Device.id)
    ).all()
    return RoomDeviceListRead(
        items=[
            RoomDeviceListItem(
                id=device.id,
                name=device.name,
                type=device.type,
                brand=device.brand,
                status=device.status,
                icon=device.icon,
                color=device.color,
                group=binding.group_name,
                favorite=binding.favorite,
                sort_order=binding.sort_order,
                updated_at=device.updated_at,
            )
            for binding, device in rows
        ],
        total=len(rows),
    )


def get_room_devices_service(
    db: Session,
    user: User,
    room_id: int,
    keyword: str | None = None,
    device_type: str | None = None,
    device_status: str | None = None,
) -> RoomDeviceListRead:
    """查询房间内设备。"""
    room = get_room_or_404(db, user, room_id)
    return list_room_devices(db, room, keyword, device_type, device_status)


def set_room_devices_service(
    db: Session, user: User, room_id: int, payload: RoomDevicesWrite
) -> RoomDeviceListRead:
    """整体替换房间的设备绑定关系。"""
    room = get_room_or_404(db, user, room_id)
    return replace_room_devices(db, room, payload)


def edit_room_device_service(
    db: Session, user: User, room_id: int, device_id: int, payload: RoomDeviceMetaWrite
) -> RoomDeviceListRead:
    """修改房间内设备的绑定元信息。"""
    room = get_room_or_404(db, user, room_id)
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
    return list_room_devices(db, room)


def update_device_service(
    db: Session, user: User, room_id: int, payload: RoomDeviceWrite
) -> RoomRead:
    """更新房间内设备状态。"""
    room = get_room_or_404(db, user, room_id)
    device = db.get(Device, payload.device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    device.status = DeviceStatus(payload.status)
    device.updated_at = datetime.now(timezone.utc)
    write_activity(db, room, f"{device.name} 状态更新为 {payload.status}")
    db.commit()
    db.refresh(room)
    return _load_room_devices(db, RoomRead.model_validate(room), room.id)


def quick_action_service(
    db: Session, user: User, room_id: int, payload: RoomQuickActionWrite
) -> RoomRead:
    """执行房间快捷操作。"""
    room = get_room_or_404(db, user, room_id)
    write_activity(db, room, f"快捷操作：{payload.action}")
    db.commit()
    db.refresh(room)
    return _load_room_devices(db, RoomRead.model_validate(room), room.id)


# === 房间场景 ===


def get_room_scenes_service(db: Session, user: User, room_id: int) -> SceneListRead:
    """查询房间关联的场景。"""
    room = get_room_or_404(db, user, room_id)
    return get_scenes_service(db, room.name, None, "all")


def preview_room_scene_service(
    db: Session, user: User, room_id: int, scene_id: str
) -> ScenePreviewRead:
    """预览房间场景动作链。"""
    get_room_or_404(db, user, room_id)
    return get_scene_preview_service(db, scene_id)


def execute_room_scene_service(
    db: Session, user: User, room_id: int, scene_id: str, payload: RoomSceneExecuteWrite
) -> SceneExecutionRead:
    """执行房间场景并记录活动日志。"""
    room = get_room_or_404(db, user, room_id)
    result = run_scene_service(db, scene_id, False, "room")
    write_activity(db, room, f"执行场景：{scene_id}", "scene")
    db.commit()
    return result
