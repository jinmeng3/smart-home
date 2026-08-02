from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class HouseholdRole(str, Enum):
    ADMIN = "admin"
    MEMBER = "member"


class HouseholdMembership(Base):
    __tablename__ = "household_memberships"
    __table_args__ = (
        UniqueConstraint("household_id", "user_id", name="uq_household_user"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    household_id: Mapped[int] = mapped_column(
        ForeignKey("households.id", ondelete="CASCADE"), comment="家庭主键"
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), comment="用户主键"
    )
    role: Mapped[HouseholdRole] = mapped_column(
        SqlEnum(HouseholdRole), default=HouseholdRole.MEMBER, comment="家庭角色"
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="加入时间"
    )

    household = relationship("Household", back_populates="memberships")
    user = relationship("User", back_populates="memberships")
