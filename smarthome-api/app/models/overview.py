from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class OverviewExecution(Base):
    __tablename__ = "overview_executions"
    __table_args__ = (
        UniqueConstraint(
            "household_id", "idempotency_key", name="uq_overview_idempotency"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True, comment="所属家庭ID"
    )
    mode: Mapped[str] = mapped_column(String(24), comment="执行模式")
    room_ids_json: Mapped[str] = mapped_column(
        Text, default="[]", comment="目标房间ID列表（JSON）"
    )
    status: Mapped[str] = mapped_column(String(24), default="queued", comment="任务状态")
    affected_device_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="受影响设备数量"
    )
    requested_by: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="请求用户ID")
    idempotency_key: Mapped[str] = mapped_column(String(128), comment="幂等键")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )


class InspectionJob(Base):
    __tablename__ = "inspection_jobs"
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True, comment="所属家庭ID"
    )
    scope: Mapped[str] = mapped_column(String(24), comment="巡检范围")
    room_ids_json: Mapped[str] = mapped_column(Text, default="[]", comment="目标房间ID列表（JSON）")
    checks_json: Mapped[str] = mapped_column(Text, default="[]", comment="检查项配置（JSON）")
    status: Mapped[str] = mapped_column(String(24), default="queued", comment="任务状态")
    device_count: Mapped[int] = mapped_column(Integer, default=0, comment="设备总数")
    checked_count: Mapped[int] = mapped_column(Integer, default=0, comment="已检查设备数")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="创建用户ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )


class HouseholdSchedule(Base):
    __tablename__ = "household_schedules"
    __table_args__ = (
        UniqueConstraint(
            "household_id", "schedule_date", name="uq_household_schedule_date"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True, comment="所属家庭ID"
    )
    schedule_date: Mapped[date] = mapped_column(Date, comment="日程日期")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    repeat_days_json: Mapped[str] = mapped_column(Text, default="[]", comment="重复星期配置（JSON）")
    targets_json: Mapped[str] = mapped_column(Text, default="{}", comment="目标配置（JSON）")
    items_json: Mapped[str] = mapped_column(Text, default="[]", comment="日程项目（JSON）")
    version: Mapped[int] = mapped_column(Integer, default=1, comment="版本号")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class DeviceSyncJob(Base):
    __tablename__ = "device_sync_jobs"
    __table_args__ = (
        UniqueConstraint(
            "household_id", "idempotency_key", name="uq_device_sync_idempotency"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True, comment="所属家庭ID"
    )
    scope: Mapped[str] = mapped_column(String(24), default="all", comment="同步范围")
    sources_json: Mapped[str] = mapped_column(Text, default="[]", comment="数据来源列表（JSON）")
    options_json: Mapped[str] = mapped_column(Text, default="{}", comment="同步选项（JSON）")
    status: Mapped[str] = mapped_column(String(24), default="queued", comment="任务状态")
    statistics_json: Mapped[str] = mapped_column(Text, default="{}", comment="同步统计（JSON）")
    idempotency_key: Mapped[str] = mapped_column(String(128), comment="幂等键")
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"), comment="创建用户ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
