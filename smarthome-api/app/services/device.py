from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.device import Device, DeviceLog
from app.schemas.device import (
    DeviceCreate,
    DeviceDetailRead,
    DeviceDetailWithLogs,
    DeviceListRead,
    DeviceLogListRead,
    DeviceLogRead,
    DeviceQueryParams,
    DeviceSyncRead,
    DeviceUpdate,
)


def get_device_or_404(db: Session, device_id: int) -> Device:
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在"
        )
    return device


def list_devices(db: Session, params: DeviceQueryParams) -> DeviceListRead:
    filters = []
    if params.keyword:
        keyword = params.keyword.strip()
        if keyword:
            filters.append(
                or_(Device.name.contains(keyword), Device.brand.contains(keyword))
            )
    if params.type:
        filters.append(Device.type == params.type)
    if params.status:
        filters.append(Device.status == params.status)
    if params.room:
        filters.append(Device.room == params.room.strip())

    total = db.scalar(select(func.count()).select_from(Device).where(*filters)) or 0
    devices = db.scalars(
        select(Device)
        .where(*filters)
        .order_by(Device.updated_at.desc())
        .offset((params.page - 1) * params.page_size)
        .limit(params.page_size)
    ).all()
    return DeviceListRead(total=total, items=list(devices))


def read_device(db: Session, device_id: int) -> DeviceDetailWithLogs:
    device = get_device_or_404(db, device_id)
    logs = db.scalars(
        select(DeviceLog)
        .where(DeviceLog.device_id == device_id)
        .order_by(DeviceLog.created_at.desc())
        .limit(20)
    ).all()
    data = DeviceDetailRead.model_validate(device).model_dump()
    return DeviceDetailWithLogs(
        **data, logs=[DeviceLogRead.model_validate(log) for log in logs]
    )


def create_device(db: Session, payload: DeviceCreate) -> Device:
    platform_id = payload.device_id or f"device-{uuid4().hex}"
    if db.scalar(select(Device.id).where(Device.device_id == platform_id)):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="设备重复"
        )

    device = Device(
        **payload.model_dump(exclude={"device_id"}),
        device_id=platform_id,
        status="offline",
    )
    db.add(device)
    db.flush()
    db.add(
        DeviceLog(device_id=device.id, action="create", message="设备创建完成")
    )
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="设备重复"
        ) from exc
    db.refresh(device)
    return device


def update_device(db: Session, device_id: int, payload: DeviceUpdate) -> Device:
    device = get_device_or_404(db, device_id)
    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(device, field, value)

    now = datetime.now(timezone.utc)
    if changes.get("status") in {"online", "running"}:
        device.last_online = now
    device.updated_at = now
    db.add(DeviceLog(device_id=device.id, action="update", message="设备信息已更新"))
    db.commit()
    db.refresh(device)
    return device


def delete_device(db: Session, device_id: int) -> None:
    device = get_device_or_404(db, device_id)
    db.delete(device)
    db.commit()


def sync_devices(db: Session, platform: str) -> DeviceSyncRead:
    devices = list(
        db.scalars(select(Device).where(Device.connection == platform)).all()
    )
    now = datetime.now(timezone.utc)
    for device in devices:
        device.last_online = now
        device.updated_at = now
        db.add(
            DeviceLog(
                device_id=device.id,
                action="sync",
                message=f"{platform} 平台同步完成",
            )
        )
    db.commit()
    return DeviceSyncRead(platform=platform, synced_count=len(devices))


def list_device_logs(
    db: Session, device_id: int, page: int, page_size: int
) -> DeviceLogListRead:
    get_device_or_404(db, device_id)
    condition = DeviceLog.device_id == device_id
    total = (
        db.scalar(select(func.count()).select_from(DeviceLog).where(condition)) or 0
    )
    logs = db.scalars(
        select(DeviceLog)
        .where(condition)
        .order_by(DeviceLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return DeviceLogListRead(total=total, items=list(logs))
