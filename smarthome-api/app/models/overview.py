from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OverviewExecution(Base):
    __tablename__ = "overview_executions"
    __table_args__ = (UniqueConstraint("household_id", "idempotency_key", name="uq_overview_idempotency"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    mode: Mapped[str] = mapped_column(String(24))
    room_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(24), default="queued")
    affected_device_count: Mapped[int] = mapped_column(Integer, default=0)
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class InspectionJob(Base):
    __tablename__ = "inspection_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(24))
    room_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    checks_json: Mapped[str] = mapped_column(Text, default="[]")
    status: Mapped[str] = mapped_column(String(24), default="queued")
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    checked_count: Mapped[int] = mapped_column(Integer, default=0)
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class HouseholdSchedule(Base):
    __tablename__ = "household_schedules"
    __table_args__ = (UniqueConstraint("household_id", "schedule_date", name="uq_household_schedule_date"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    schedule_date: Mapped[date] = mapped_column(Date)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    repeat_days_json: Mapped[str] = mapped_column(Text, default="[]")
    targets_json: Mapped[str] = mapped_column(Text, default="{}")
    items_json: Mapped[str] = mapped_column(Text, default="[]")
    version: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DeviceSyncJob(Base):
    __tablename__ = "device_sync_jobs"
    __table_args__ = (UniqueConstraint("household_id", "idempotency_key", name="uq_device_sync_idempotency"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    household_id: Mapped[int] = mapped_column(ForeignKey("households.id", ondelete="CASCADE"), index=True)
    scope: Mapped[str] = mapped_column(String(24), default="all")
    sources_json: Mapped[str] = mapped_column(Text, default="[]")
    options_json: Mapped[str] = mapped_column(Text, default="{}")
    status: Mapped[str] = mapped_column(String(24), default="queued")
    statistics_json: Mapped[str] = mapped_column(Text, default="{}")
    idempotency_key: Mapped[str] = mapped_column(String(128))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
