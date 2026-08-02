from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.membership import HouseholdMembership


class Household(Base):
    __tablename__ = "households"

    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    name: Mapped[str] = mapped_column(String(80), comment="家庭名称")
    address: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="家庭地址"
    )
    timezone: Mapped[str] = mapped_column(
        String(64), default="Asia/Shanghai", comment="所在时区"
    )
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), comment="创建用户主键"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="创建时间"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )

    memberships: Mapped[list[HouseholdMembership]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )
