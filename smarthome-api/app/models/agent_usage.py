from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentUsage(Base):
    """Agent 使用统计：记录每次运行的 token 用量和成本。"""

    __tablename__ = "agent_usage"
    __table_args__ = (
        Index("ix_agent_usage_user_date", "user_id", "created_at"),
        UniqueConstraint("run_id", name="uq_agent_usage_run_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    household_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("households.id", ondelete="CASCADE"), nullable=False
    )
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, comment="运行 ID")
    model_name: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="模型名称"
    )
    input_tokens: Mapped[int] = mapped_column(
        Integer, default=0, comment="输入 token 数"
    )
    output_tokens: Mapped[int] = mapped_column(
        Integer, default=0, comment="输出 token 数"
    )
    tool_call_count: Mapped[int] = mapped_column(
        Integer, default=0, comment="工具调用次数"
    )
    status: Mapped[str] = mapped_column(
        String(24), default="completed", comment="运行状态"
    )
    error_message: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="错误信息"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )


class AgentUsageDaily(Base):
    """每日用量汇总，用于预算检查。"""

    __tablename__ = "agent_usage_daily"
    __table_args__ = (
        UniqueConstraint("user_id", "date", name="uq_agent_usage_daily_user_date"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    date: Mapped[str] = mapped_column(
        String(10), nullable=False, comment="日期 YYYY-MM-DD"
    )
    total_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    run_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
