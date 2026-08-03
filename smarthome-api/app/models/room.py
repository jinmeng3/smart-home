from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
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
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
