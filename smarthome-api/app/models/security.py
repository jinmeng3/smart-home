from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SecurityDevice(Base):
    __tablename__ = "user_security_devices"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    device_name: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="设备名称"
    )
    location: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="登录位置/平台"
    )
    last_active_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="最后活跃时间",
    )
    trusted: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否受信任"
    )
    is_current: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, comment="是否为当前设备"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )


class SecurityLog(Base):
    __tablename__ = "user_security_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    title: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="日志标题"
    )
    detail: Mapped[str] = mapped_column(
        Text, nullable=False, comment="日志详情"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="记录时间",
    )