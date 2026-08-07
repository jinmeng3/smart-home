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


class Scene(Base):
    __tablename__ = "scenes"
    __table_args__ = (
        Index("ix_scenes_household_sort", "household_id", "sort_order"),
        Index("ix_scenes_household_updated", "household_id", "updated_at"),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="场景ID（主键）")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(80), comment="场景名称")
    description: Mapped[str] = mapped_column(String(500), default="", comment="场景描述")
    icon: Mapped[str] = mapped_column(String(64), default="home", comment="图标名称")
    color: Mapped[str] = mapped_column(String(120), default="var(--color-primary-600)", comment="主题颜色")
    trigger_type: Mapped[str] = mapped_column(String(20), default="manual", comment="触发类型")
    trigger_label: Mapped[str] = mapped_column(String(255), default="手动执行", comment="触发方式说明")
    device_count: Mapped[int] = mapped_column(Integer, default=0, comment="涉及设备数量")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    recommended: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否推荐")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值")
    room_names: Mapped[str | None] = mapped_column(Text, nullable=True, comment="关联房间名称列表（JSON）")
    monthly_execute_count: Mapped[int] = mapped_column(Integer, default=0, comment="本月执行次数")
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="最后执行时间")
    high_risk: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否高风险场景")
    source_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True, comment="来源模板ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )

    steps: Mapped[list[SceneStep]] = relationship(
        back_populates="scene",
        cascade="all, delete-orphan",
        order_by="SceneStep.step_order",
    )
    execution_logs: Mapped[list[SceneExecutionLog]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )


class SceneStep(Base):
    __tablename__ = "scene_steps"

    id: Mapped[str] = mapped_column(String(96), primary_key=True, comment="步骤ID（主键）")
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), index=True, comment="所属场景ID"
    )
    name: Mapped[str] = mapped_column(String(120), comment="步骤名称")
    description: Mapped[str] = mapped_column(String(500), default="", comment="步骤描述")
    device_id: Mapped[str] = mapped_column(String(120), comment="目标设备ID")
    step_order: Mapped[int] = mapped_column(Integer, comment="执行顺序")

    scene: Mapped[Scene] = relationship(back_populates="steps")


class SceneRoom(Base):
    __tablename__ = "scene_rooms"
    __table_args__ = (
        UniqueConstraint("scene_id", "room_id", name="uq_scene_room"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"), nullable=False, index=True
    )


class SceneTemplate(Base):
    __tablename__ = "scene_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, comment="模板ID（主键）")
    name: Mapped[str] = mapped_column(String(80), comment="模板名称")
    description: Mapped[str] = mapped_column(String(500), default="", comment="模板描述")
    icon: Mapped[str] = mapped_column(String(64), default="layers", comment="图标名称")
    color: Mapped[str] = mapped_column(String(120), default="var(--color-primary-600)", comment="主题颜色")
    trigger_type: Mapped[str] = mapped_column(String(20), default="manual", comment="触发类型")
    trigger_label: Mapped[str] = mapped_column(String(255), default="手动执行", comment="触发方式说明")
    category: Mapped[str] = mapped_column(String(40), default="其他", comment="模板分类")
    room_labels: Mapped[str] = mapped_column(Text, default="[]", comment="适用房间标签（JSON）")
    device_count: Mapped[int] = mapped_column(Integer, default=0, comment="涉及设备数量")
    recommended: Mapped[bool] = mapped_column(Boolean, default=False, comment="是否推荐")
    steps_json: Mapped[str] = mapped_column(Text, default="[]", comment="步骤配置（JSON）")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, comment="是否启用")
    sort_order: Mapped[int] = mapped_column(Integer, default=0, comment="排序值")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )


class SceneExecutionLog(Base):
    __tablename__ = "scene_execution_logs"

    id: Mapped[str] = mapped_column(String(96), primary_key=True, comment="执行日志ID（主键）")
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), index=True, comment="所属场景ID"
    )
    status: Mapped[str] = mapped_column(String(20), default="running", comment="执行状态")
    source: Mapped[str] = mapped_column(String(40), default="manual", comment="触发来源")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="开始时间"
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="结束时间")
    message: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="结果消息")

    scene: Mapped[Scene] = relationship(back_populates="execution_logs")
    steps: Mapped[list[SceneExecutionStep]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )


class SceneExecutionStep(Base):
    __tablename__ = "scene_execution_steps"

    id: Mapped[str] = mapped_column(String(120), primary_key=True, comment="步骤执行ID（主键）")
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("scene_execution_logs.id", ondelete="CASCADE"), index=True, comment="所属执行日志ID"
    )
    step_id: Mapped[str] = mapped_column(String(96), comment="对应场景步骤ID")
    status: Mapped[str] = mapped_column(String(20), default="pending", comment="执行状态")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="开始时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="结束时间")
    message: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="结果消息")

    execution: Mapped[SceneExecutionLog] = relationship(back_populates="steps")


class SceneDraft(Base):
    __tablename__ = "scene_drafts"

    id: Mapped[str] = mapped_column(String(96), primary_key=True, comment="草稿ID（主键）")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    payload_json: Mapped[str] = mapped_column(Text, comment="表单数据快照（JSON）")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新时间"
    )
