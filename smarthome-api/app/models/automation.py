from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Automation(Base):
    __tablename__ = "automations"
    __table_args__ = (
        UniqueConstraint("household_id", "name", name="uq_automation_household_name"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True, comment="主键")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), index=True, comment="所属家庭ID"
    )
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="自动化名称")
    description: Mapped[str] = mapped_column(
        String(100), default="", nullable=False, comment="描述"
    )
    trigger_type: Mapped[str] = mapped_column(
        String(32), default="manual", nullable=False, comment="触发类型（manual/device/schedule等）"
    )
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, comment="是否启用")
    priority: Mapped[int] = mapped_column(Integer, default=2, nullable=False, comment="优先级")
    cooldown_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="冷却时间（秒）"
    )
    delay_seconds: Mapped[int] = mapped_column(
        Integer, default=0, nullable=False, comment="延迟执行时间（秒）"
    )
    note: Mapped[str] = mapped_column(String(100), default="", nullable=False, comment="备注")
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), comment="创建者ID"
    )
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False, comment="版本号")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    triggers: Mapped[list[AutomationTrigger]] = relationship(
        cascade="all, delete-orphan"
    )
    conditions: Mapped[list[AutomationCondition]] = relationship(
        cascade="all, delete-orphan"
    )
    actions: Mapped[list[AutomationAction]] = relationship(cascade="all, delete-orphan")
    executions: Mapped[list[AutomationExecution]] = relationship(
        cascade="all, delete-orphan"
    )


class AutomationTrigger(Base):
    __tablename__ = "automation_triggers"
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    automation_id: Mapped[int] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"), index=True, comment="所属自动化ID"
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False, comment="触发类型")
    config_json: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False, comment="触发配置（JSON）"
    )


class AutomationCondition(Base):
    __tablename__ = "automation_conditions"
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    automation_id: Mapped[int] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"), index=True, comment="所属自动化ID"
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False, comment="条件类型")
    config_json: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False, comment="条件配置（JSON）"
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, comment="排序位置")


class AutomationAction(Base):
    __tablename__ = "automation_actions"
    __table_args__ = (
        UniqueConstraint(
            "automation_id", "position", name="uq_automation_action_position"
        ),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    automation_id: Mapped[int] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"), index=True, comment="所属自动化ID"
    )
    type: Mapped[str] = mapped_column(String(32), nullable=False, comment="动作类型")
    device_id: Mapped[int | None] = mapped_column(
        ForeignKey("devices.id", ondelete="SET NULL"), nullable=True, comment="目标设备ID"
    )
    scene_id: Mapped[str | None] = mapped_column(
        ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True, comment="目标场景ID"
    )
    config_json: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False, comment="动作配置（JSON）"
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False, comment="排序位置")


class AutomationExecution(Base):
    __tablename__ = "automation_executions"
    __table_args__ = (
        Index("ix_automation_execution_status_time", "status", "started_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    automation_id: Mapped[int] = mapped_column(
        ForeignKey("automations.id", ondelete="CASCADE"), index=True, comment="所属自动化ID"
    )
    source: Mapped[str] = mapped_column(String(32), nullable=False, comment="触发来源")
    status: Mapped[str] = mapped_column(String(24), nullable=False, comment="执行状态")
    trigger_snapshot: Mapped[str] = mapped_column(
        Text, default="{}", nullable=False, comment="触发时配置快照（JSON）"
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True, comment="执行耗时（毫秒）")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True, comment="错误信息")
    idempotency_key: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, comment="幂等键"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="开始时间"
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="结束时间"
    )
