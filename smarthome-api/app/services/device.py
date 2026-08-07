from datetime import datetime, timezone
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.device import Device, DeviceGroup, DeviceLog, DeviceStatus
from app.schemas.device import (
    DeviceBatchGroup,
    DeviceBatchGroupResult,
    DeviceCreate,
    DeviceDetailRead,
    DeviceDetailWithLogs,
    DeviceImageRead,
    DeviceListRead,
    DeviceLogListRead,
    DeviceLogRead,
    DevicePlatform,
    DeviceQueryParams,
    DeviceSyncRead,
    DeviceUpdate,
)

IMAGE_EXTENSION_BY_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


def get_device_or_404(db: Session, device_id: int) -> Device:
    """按主键获取设备，并统一处理不存在的情况。"""
    device = db.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    return device


# === 设备 CRUD ===


def list_devices_service(db: Session, params: DeviceQueryParams) -> DeviceListRead:
    """组合设备筛选条件并返回分页结果。"""
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


def get_device_service(db: Session, device_id: int) -> DeviceDetailWithLogs:
    """返回设备详情及最近二十条操作日志。"""
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


def add_device_service(db: Session, payload: DeviceCreate) -> Device:
    """创建设备和首条日志，使用同一个事务保证数据一致性。"""
    platform_id = payload.device_id or f"device-{uuid4().hex}"
    if db.scalar(select(Device.id).where(Device.device_id == platform_id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="设备重复")

    device = Device(
        **payload.model_dump(exclude={"device_id"}),
        device_id=platform_id,
        status=DeviceStatus.OFFLINE,
    )
    db.add(device)
    db.flush()
    db.add(DeviceLog(device_id=device.id, action="create", message="设备创建完成"))
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="设备重复"
        ) from exc
    db.refresh(device)
    return device


def update_device_service(db: Session, device_id: int, payload: DeviceUpdate) -> Device:
    """更新传入字段，并在设备上线时刷新最后在线时间。"""
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


def delete_device_service(db: Session, device_id: int) -> None:
    """删除设备，关联日志由 ORM 级联清理。"""
    device = get_device_or_404(db, device_id)
    db.delete(device)
    db.commit()


# === 设备同步 ===


def sync_devices_service(db: Session, platform: DevicePlatform) -> DeviceSyncRead:
    """刷新指定平台的本地设备状态；平台适配器可在此处接入。"""
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


# === 设备日志 ===


def list_device_logs_service(
    db: Session, device_id: int, page: int, page_size: int
) -> DeviceLogListRead:
    """按创建时间倒序返回指定设备的分页日志。"""
    get_device_or_404(db, device_id)
    condition = DeviceLog.device_id == device_id
    total = db.scalar(select(func.count()).select_from(DeviceLog).where(condition)) or 0
    logs = db.scalars(
        select(DeviceLog)
        .where(condition)
        .order_by(DeviceLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return DeviceLogListRead(total=total, items=list(logs))


# === 设备图片 ===


def upload_image_service(
    db: Session, device_id: int | None, file: UploadFile, settings: Settings
) -> DeviceImageRead:
    """校验并保存设备图片，可选关联设备并更新其 image_url，返回访问地址。"""
    device = get_device_or_404(db, device_id) if device_id is not None else None
    extension = IMAGE_EXTENSION_BY_TYPE.get(file.content_type or "")
    if file.content_type not in settings.allowed_device_image_types or not extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PNG, JPG, and WEBP images are supported",
        )

    content = file.file.read()

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Image file cannot be empty"
        )

    if len(content) > settings.max_device_image_size:
        raise HTTPException(
            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
            detail="Image file is too large",
        )

    settings.device_image_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{extension}"
    image_path = settings.device_image_dir / filename
    image_path.write_bytes(content)
    image_url = f"/uploads/devices/{filename}"

    if device is not None:
        device.image_url = image_url
        db.commit()
    return DeviceImageRead(
        image_url=image_url,
        original_name=file.filename or "image",
        mime_type=file.content_type or "application/octet-stream",
        size_bytes=len(content),
    )


# === 设备分组 ===


def batch_group_devices_service(
    db: Session, payload: DeviceBatchGroup
) -> DeviceBatchGroupResult:
    """创建或复用分组，将指定设备分配到该分组。"""
    group = db.scalar(select(DeviceGroup).where(DeviceGroup.name == payload.group))
    if not group:
        group = DeviceGroup(name=payload.group)
        db.add(group)
        db.flush()

    assigned_count = 0
    if payload.device_ids:
        devices = db.scalars(
            select(Device).where(Device.id.in_(payload.device_ids))
        ).all()

        for device in devices:
            device.group_id = group.id
            device.updated_at = datetime.now(timezone.utc)
            db.add(
                DeviceLog(
                    device_id=device.id,
                    action="group",
                    message=f"已分配到分组「{group.name}」",
                )
            )
            assigned_count += 1

    db.commit()
    return DeviceBatchGroupResult(
        group_id=group.id, group=group.name, assigned_count=assigned_count
    )


# === 设备数据 ===


def list_device_data_service(db: Session, device_id: int):
    """获取设备数据。"""
    pass
