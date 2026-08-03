from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Scene(Base):
    __tablename__ = "scenes"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500), default="")
    icon: Mapped[str] = mapped_column(String(64), default="home")
    color: Mapped[str] = mapped_column(String(120), default="var(--color-primary-600)")
    trigger_type: Mapped[str] = mapped_column(String(20), default="manual")
    trigger_label: Mapped[str] = mapped_column(String(255), default="手动执行")
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    room_names: Mapped[str | None] = mapped_column(Text, nullable=True)
    monthly_execute_count: Mapped[int] = mapped_column(Integer, default=0)
    last_executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    high_risk: Mapped[bool] = mapped_column(Boolean, default=False)
    source_template_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
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

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(String(500), default="")
    device_id: Mapped[str] = mapped_column(String(120))
    step_order: Mapped[int] = mapped_column(Integer)

    scene: Mapped[Scene] = relationship(back_populates="steps")


class SceneTemplate(Base):
    __tablename__ = "scene_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    description: Mapped[str] = mapped_column(String(500), default="")
    icon: Mapped[str] = mapped_column(String(64), default="layers")
    color: Mapped[str] = mapped_column(String(120), default="var(--color-primary-600)")
    trigger_type: Mapped[str] = mapped_column(String(20), default="manual")
    trigger_label: Mapped[str] = mapped_column(String(255), default="手动执行")
    category: Mapped[str] = mapped_column(String(40), default="其他")
    room_labels: Mapped[str] = mapped_column(Text, default="[]")
    device_count: Mapped[int] = mapped_column(Integer, default=0)
    recommended: Mapped[bool] = mapped_column(Boolean, default=False)
    steps_json: Mapped[str] = mapped_column(Text, default="[]")
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class SceneExecutionLog(Base):
    __tablename__ = "scene_execution_logs"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    scene_id: Mapped[str] = mapped_column(
        ForeignKey("scenes.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(20), default="running")
    source: Mapped[str] = mapped_column(String(40), default="manual")
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    scene: Mapped[Scene] = relationship(back_populates="execution_logs")
    steps: Mapped[list[SceneExecutionStep]] = relationship(
        back_populates="execution", cascade="all, delete-orphan"
    )


class SceneExecutionStep(Base):
    __tablename__ = "scene_execution_steps"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    execution_id: Mapped[str] = mapped_column(
        ForeignKey("scene_execution_logs.id", ondelete="CASCADE"), index=True
    )
    step_id: Mapped[str] = mapped_column(String(96))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message: Mapped[str | None] = mapped_column(String(500), nullable=True)

    execution: Mapped[SceneExecutionLog] = relationship(back_populates="steps")


class SceneDraft(Base):
    __tablename__ = "scene_drafts"

    id: Mapped[str] = mapped_column(String(96), primary_key=True)
    payload_json: Mapped[str] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
