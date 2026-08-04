import json
from datetime import date, datetime, time, timezone

from fastapi import HTTPException
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.device import Device
from app.models.room import Room, RoomActivityLog, RoomDevice, RoomEnvironmentSample, RoomPreference
from app.schemas.room import (
    EnvironmentLatestRead, EnvironmentPoint, EnvironmentTrendRead, RoomDeviceListItem,
    RoomDeviceListRead, RoomDevicesWrite, RoomLogListRead, RoomLogRead, RoomWrite,
)


def replace_bindings(db: Session, room: Room, device_ids: list[int]) -> None:
    devices = list(db.scalars(select(Device).where(Device.id.in_(device_ids))).all()) if device_ids else []
    if len(devices) != len(set(device_ids)):
        raise HTTPException(status_code=422, detail="部分设备不存在")
    db.query(RoomDevice).filter(RoomDevice.room_id == room.id).delete(synchronize_session=False)
    for index, device in enumerate(devices):
        device.room = room.name
        db.add(RoomDevice(room_id=room.id, device_id=device.id, sort_order=index))
    room.device_count = len(devices)
    room.online_count = sum(device.status in {"online", "running"} for device in devices)


def save_room(db: Session, household_id: int, payload: RoomWrite, room: Room | None = None) -> Room:
    duplicate = db.scalar(select(Room).where(Room.household_id == household_id, Room.name == payload.name, Room.id != (room.id if room else -1)))
    if duplicate:
        raise HTTPException(status_code=409, detail="同一家庭内房间名称不能重复")
    is_new = room is None
    if room is None:
        room = Room(household_id=household_id, name=payload.name)
        db.add(room)
        db.flush()
    elif payload.version is not None and payload.version != room.version:
        raise HTTPException(status_code=409, detail="房间版本冲突")
    room.name, room.floor, room.room_type = payload.name, payload.floor, payload.room_type
    room.icon, room.theme_color = payload.icon, payload.theme_color
    room.version = 1 if is_new else room.version + 1
    replace_bindings(db, room, payload.device_ids)
    preference = db.get(RoomPreference, room.id) or RoomPreference(room_id=room.id)
    for field, value in payload.preferences.model_dump().items():
        setattr(preference, field, value)
    db.add(preference)
    db.commit()
    db.refresh(room)
    return room


def write_activity(db: Session, room: Room, event: str, source: str = "manual", device_id: int | None = None) -> None:
    db.add(RoomActivityLog(room_id=room.id, device_id=device_id, source=source, event=event, tags_json=json.dumps([room.name], ensure_ascii=False)))


def list_room_logs(db: Session, room: Room, page: int, page_size: int, keyword: str | None, date_from: date | None, date_to: date | None) -> RoomLogListRead:
    filters = [RoomActivityLog.room_id == room.id]
    if keyword:
        filters.append(RoomActivityLog.event.like(f"%{keyword.strip()}%"))
    if date_from:
        filters.append(RoomActivityLog.occurred_at >= datetime.combine(date_from, time.min, tzinfo=timezone.utc))
    if date_to:
        filters.append(RoomActivityLog.occurred_at <= datetime.combine(date_to, time.max, tzinfo=timezone.utc))
    total = db.scalar(select(func.count()).select_from(RoomActivityLog).where(*filters)) or 0
    rows = db.execute(select(RoomActivityLog, Device.name).outerjoin(Device, Device.id == RoomActivityLog.device_id).where(*filters).order_by(RoomActivityLog.occurred_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return RoomLogListRead(total=total, items=[RoomLogRead(id=log.id, occurred_at=log.occurred_at, source=log.source, event=log.event, result=log.result, duration_ms=log.duration_ms, device_id=log.device_id, device_name=name, tags=json.loads(log.tags_json), detail=json.loads(log.detail_json)) for log, name in rows])


def replace_room_devices(db: Session, room: Room, payload: RoomDevicesWrite) -> RoomDeviceListRead:
    ids = [item.device_id for item in payload.devices]
    devices = {item.id: item for item in db.scalars(select(Device).where(Device.id.in_(ids))).all()}
    if set(ids) != devices.keys():
        raise HTTPException(status_code=422, detail="部分设备不存在")
    db.query(RoomDevice).filter(RoomDevice.room_id == room.id).delete(synchronize_session=False)
    for item in payload.devices:
        devices[item.device_id].room = room.name
        db.add(RoomDevice(room_id=room.id, device_id=item.device_id, group_name=item.group, favorite=item.favorite, sort_order=item.sort_order))
    room.device_count = len(ids)
    room.online_count = sum(devices[item].status in {"online", "running"} for item in ids)
    db.commit()
    return list_room_devices(db, room)


def list_room_devices(db: Session, room: Room, keyword: str | None = None, device_type: str | None = None, device_status: str | None = None) -> RoomDeviceListRead:
    filters = [RoomDevice.room_id == room.id]
    if keyword:
        filters.append(or_(Device.name.like(f"%{keyword.strip()}%"), Device.brand.like(f"%{keyword.strip()}%")))
    if device_type:
        filters.append(Device.type == device_type)
    if device_status:
        filters.append(Device.status == device_status)
    rows = db.execute(select(RoomDevice, Device).join(Device).where(*filters).order_by(RoomDevice.sort_order, Device.id)).all()
    return RoomDeviceListRead(items=[RoomDeviceListItem(id=device.id, name=device.name, type=device.type, brand=device.brand, status=device.status, group=binding.group_name, favorite=binding.favorite, sort_order=binding.sort_order) for binding, device in rows], total=len(rows))


def latest_environment(db: Session, room: Room) -> EnvironmentLatestRead:
    sample = db.scalar(select(RoomEnvironmentSample).where(RoomEnvironmentSample.room_id == room.id).order_by(RoomEnvironmentSample.sampled_at.desc()))
    return EnvironmentLatestRead(temperature=sample.temperature if sample else room.temperature, humidity=sample.humidity if sample else room.humidity, pm25=sample.pm25 if sample else room.pm25, illuminance=sample.illuminance if sample else room.illuminance, noise=sample.noise if sample else room.noise, comfort=room.comfort, sampled_at=sample.sampled_at if sample else room.updated_at)


def environment_trends(db: Session, room: Room, metrics: list[str]) -> EnvironmentTrendRead:
    allowed = {"temperature", "humidity", "pm25", "illuminance", "noise"}
    if not metrics or not set(metrics) <= allowed:
        raise HTTPException(status_code=422, detail="环境指标不合法")
    samples = list(db.scalars(select(RoomEnvironmentSample).where(RoomEnvironmentSample.room_id == room.id).order_by(RoomEnvironmentSample.sampled_at.desc()).limit(288)).all())
    if not samples:
        latest = latest_environment(db, room)
        return EnvironmentTrendRead(metrics=metrics, items=[EnvironmentPoint(sampled_at=latest.sampled_at, values={metric: float(getattr(latest, metric)) for metric in metrics})])
    return EnvironmentTrendRead(metrics=metrics, items=[EnvironmentPoint(sampled_at=item.sampled_at, values={metric: float(getattr(item, metric)) for metric in metrics}) for item in reversed(samples)])
