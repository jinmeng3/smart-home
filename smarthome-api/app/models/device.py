from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class DeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    WARNING = "warning"
    RUNNING = "running"


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (
        Index("ix_devices_household_status", "household_id", "status"),
        Index("ix_devices_household_updated", "household_id", "updated_at"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键"
    )
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属家庭ID",
    )
    device_id: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True, comment="设备标识"
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False, comment="设备名称")
    room: Mapped[str] = mapped_column(
        String(80), nullable=False, index=True, comment="所在房间"
    )
    type: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="设备类型"
    )
    brand: Mapped[str] = mapped_column(String(64), nullable=False, comment="设备品牌")
    status: Mapped[DeviceStatus] = mapped_column(
        Enum(DeviceStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="设备状态",
    )
    connection: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True, comment="连接方式"
    )
    firmware: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="固件版本"
    )
    icon: Mapped[str] = mapped_column(
        String(64), default="device-management", comment="设备图标"
    )
    color: Mapped[str] = mapped_column(
        String(16), default="#6b7280", comment="设备颜色"
    )
    image_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="设备图片地址"
    )
    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("device_group.id"),
        index=True,
        nullable=True,
        comment="所属分组",
    )
    last_online: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后在线时间"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    logs: Mapped[list[DeviceLog]] = relationship(
        back_populates="device", cascade="all, delete-orphan"
    )

    group: Mapped[DeviceGroup | None] = relationship(back_populates="devices")


class DeviceGroup(Base):
    __tablename__ = "device_group"
    __table_args__ = (
        UniqueConstraint("household_id", "name", name="uq_device_group_household_name"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键"
    )
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属家庭ID",
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False, comment="分组名称")
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="分组描述"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )

    devices: Mapped[list[Device]] = relationship(back_populates="group")


class DeviceLog(Base):
    __tablename__ = "device_logs"

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键"
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="设备主键",
    )
    action: Mapped[str] = mapped_column(String(64), nullable=False, comment="操作类型")
    message: Mapped[str] = mapped_column(Text, nullable=False, comment="日志内容")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )

    device: Mapped[Device] = relationship(back_populates="logs")
