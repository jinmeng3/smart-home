from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentRunLease(Base):
    """Agent 运行租约：防止同一会话并发运行。"""

    __tablename__ = "agent_run_lease"
    __table_args__ = (
        UniqueConstraint(
            "user_id", "household_id", "session_id",
            name="uq_agent_lease_user_household_session",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="用户 ID"
    )
    household_id: Mapped[int] = mapped_column(
        Integer, nullable=False, comment="家庭 ID"
    )
    session_id: Mapped[int] = mapped_column(
        Integer, nullable=False, index=True, comment="会话主键"
    )
    run_id: Mapped[str] = mapped_column(
        String(64), nullable=False, comment="运行 ID"
    )
    thread_id: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="checkpointer thread ID"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="租约创建时间"
    )