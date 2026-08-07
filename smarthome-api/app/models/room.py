from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint("household_id", "name", name="unique_room_name"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True, autoincrement=True, comment="主键"
    )
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
        comment="所属家庭ID",
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False, comment="房间名称")
    floor: Mapped[str] = mapped_column(
        String(40), default="1F", nullable=False, comment="所在楼层"
    )
    room_type: Mapped[str] = mapped_column(
        String(32), default="living", nullable=False, comment="房间类型"
    )
    image_url: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="房间图片地址"
    )
    icon: Mapped[str] = mapped_column(
        String(40), default="room", nullable=False, comment="房间图标"
    )
    theme_color: Mapped[str] = mapped_column(
        String(16), default="#3478f6", nullable=False, comment="主题颜色"
    )
    version: Mapped[int] = mapped_column(
        Integer, default=1, nullable=False, comment="版本号"
    )
    area: Mapped[float] = mapped_column(
        Float, default=0, nullable=False, comment="面积（平方米）"
    )
    comfort: Mapped[int] = mapped_column(
        Integer, default=80, nullable=False, comment="舒适度评分"
    )
    device_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="设备总数"
    )
    online_count: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="在线设备数"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="更新时间",
    )


class RoomDevice(Base):
    __tablename__ = "room_devices"
    __table_args__ = (UniqueConstraint("room_id", "device_id", name="uq_room_device"),)
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True, comment="所属房间ID"
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True, comment="关联设备ID"
    )
    group_name: Mapped[str] = mapped_column(
        String(80), default="未分组", nullable=False, comment="设备分组名称"
    )
    favorite: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, comment="是否收藏"
    )
    sort_order: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="排序值"
    )


class RoomActivityLog(Base):
    __tablename__ = "room_activity_logs"
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True, comment="所属房间ID"
    )
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联设备ID",
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, comment="操作来源")
    event: Mapped[str] = mapped_column(String(120), nullable=False, comment="事件描述")
    result: Mapped[str] = mapped_column(
        String(24), default="success", nullable=False, comment="执行结果"
    )
    duration_ms: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="执行耗时（毫秒）"
    )
    tags_json: Mapped[str] = mapped_column(
        Text, default="[]", nullable=False, comment="标签列表（JSON）"
    )
    detail_json: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False, comment="详情数据（JSON）"
    )
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        comment="发生时间",
    )

