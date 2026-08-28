from datetime import datetime, timezone
from app.utils.time import now_utc

from fastapi import HTTPException, status
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.models.security import SecurityDevice, SecurityLog
from app.models.user import User
from app.schemas.security import (
    SecurityDeviceRead,
    SecurityLogCreate,
    SecurityLogRead,
    SecurityMetaRead,
)


def get_security_meta(db: Session, user: User) -> SecurityMetaRead:
    """获取安全元数据：登录设备列表 + 安全日志 + 密码更新时间。"""
    devices = db.scalars(
        select(SecurityDevice)
        .where(SecurityDevice.user_id == user.id)
        .order_by(desc(SecurityDevice.is_current), desc(SecurityDevice.last_active_at))
    ).all()

    logs = db.scalars(
        select(SecurityLog)
        .where(SecurityLog.user_id == user.id)
        .order_by(desc(SecurityLog.created_at))
        .limit(20)
    ).all()

    # 从最近一条"已修改密码"日志推导密码更新时间
    password_log = db.scalar(
        select(SecurityLog)
        .where(
            SecurityLog.user_id == user.id,
            SecurityLog.title == "已修改密码",
        )
        .order_by(desc(SecurityLog.created_at))
        .limit(1)
    )

    return SecurityMetaRead(
        password_updated_at=password_log.created_at if password_log else None,
        devices=[SecurityDeviceRead.model_validate(d) for d in devices],
        logs=[SecurityLogRead.model_validate(l) for l in logs],
    )


def create_security_log(
    db: Session, user: User, payload: SecurityLogCreate
) -> SecurityLogRead:
    """记录一条安全日志。"""
    log = SecurityLog(user_id=user.id, title=payload.title, detail=payload.detail)
    db.add(log)
    db.commit()
    db.refresh(log)
    return SecurityLogRead.model_validate(log)


def update_device_trust(
    db: Session, user: User, device_id: int, trusted: bool
) -> SecurityDeviceRead:
    """更新设备信任状态。"""
    device = db.scalar(
        select(SecurityDevice).where(
            SecurityDevice.id == device_id,
            SecurityDevice.user_id == user.id,
        )
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    device.trusted = trusted
    db.commit()
    db.refresh(device)
    return SecurityDeviceRead.model_validate(device)


def revoke_device(db: Session, user: User, device_id: int) -> None:
    """移除登录设备（当前设备不可移除）。"""
    device = db.scalar(
        select(SecurityDevice).where(
            SecurityDevice.id == device_id,
            SecurityDevice.user_id == user.id,
        )
    )
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="设备不存在")
    if device.is_current:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="不能移除当前设备",
        )
    db.delete(device)
    db.commit()


def register_current_device(
    db: Session,
    user: User,
    device_name: str,
    location: str,
) -> SecurityDevice:
    """登录成功后注册或更新当前设备记录。"""
    now = now_utc()

    # 清空当前用户的旧 is_current 标记
    current_devices = db.scalars(
        select(SecurityDevice).where(
            SecurityDevice.user_id == user.id,
            SecurityDevice.is_current.is_(True),
        )
    ).all()
    for device in current_devices:
        device.is_current = False

    # 查找是否已有相同设备名 + 位置的记录
    existing = db.scalar(
        select(SecurityDevice).where(
            SecurityDevice.user_id == user.id,
            SecurityDevice.device_name == device_name,
            SecurityDevice.location == location,
        )
    )

    if existing:
        existing.is_current = True
        existing.last_active_at = now
        db.commit()
        db.refresh(existing)
        return existing

    device = SecurityDevice(
        user_id=user.id,
        device_name=device_name,
        location=location,
        last_active_at=now,
        trusted=True,
        is_current=True,
    )
    db.add(device)
    db.commit()
    db.refresh(device)
    return device
