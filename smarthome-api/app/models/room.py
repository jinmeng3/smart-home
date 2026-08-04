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

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    floor: Mapped[str] = mapped_column(String(40), default="1F", nullable=False)
    room_type: Mapped[str] = mapped_column(String(32), default="living", nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    icon: Mapped[str] = mapped_column(String(40), default="room", nullable=False)
    theme_color: Mapped[str] = mapped_column(
        String(16), default="#3478f6", nullable=False
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    area: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    comfort: Mapped[int] = mapped_column(Integer, default=80, nullable=False)
    temperature: Mapped[float] = mapped_column(Float, default=24, nullable=False)
    humidity: Mapped[int] = mapped_column(Integer, default=55, nullable=False)
    pm25: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    illuminance: Mapped[int] = mapped_column(Integer, default=320, nullable=False)
    noise: Mapped[int] = mapped_column(Integer, default=42, nullable=False)
    device_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    online_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    device_states: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class RoomDevice(Base):
    __tablename__ = "room_devices"
    __table_args__ = (UniqueConstraint("room_id", "device_id", name="uq_room_device"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    device_id: Mapped[int] = mapped_column(
        ForeignKey("devices.id", ondelete="CASCADE"), index=True
    )
    group_name: Mapped[str] = mapped_column(
        String(80), default="未分组", nullable=False
    )
    favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class RoomPreference(Base):
    __tablename__ = "room_preferences"
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), primary_key=True
    )
    pin_common_devices: Mapped[bool] = mapped_column(Boolean, default=True)
    show_environment: Mapped[bool] = mapped_column(Boolean, default=True)
    show_scene_entry: Mapped[bool] = mapped_column(Boolean, default=True)


class RoomActivityLog(Base):
    __tablename__ = "room_activity_logs"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), nullable=True
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False)
    event: Mapped[str] = mapped_column(String(120), nullable=False)
    result: Mapped[str] = mapped_column(String(24), default="success", nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tags_json: Mapped[str] = mapped_column(Text, default="[]", nullable=False)
    detail_json: Mapped[str] = mapped_column(Text, default="{}", nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class RoomEnvironmentSample(Base):
    __tablename__ = "room_environment_samples"
    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    temperature: Mapped[float] = mapped_column(Float)
    humidity: Mapped[int] = mapped_column(Integer)
    pm25: Mapped[int] = mapped_column(Integer)
    illuminance: Mapped[int] = mapped_column(Integer)
    noise: Mapped[int] = mapped_column(Integer)
    sampled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )


class RoomEnvironmentReport(Base):
    __tablename__ = "room_environment_reports"
    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(24), default="queued")
    download_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
