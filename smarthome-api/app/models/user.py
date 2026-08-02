from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.membership import HouseholdMembership


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    name: Mapped[str] = mapped_column(String(50), comment="用户名称")
    email: Mapped[str] = mapped_column(
        String(255), unique=True, index=True, comment="电子邮箱"
    )
    password_hash: Mapped[str] = mapped_column(
        String(255), nullable=False, comment="密码哈希"
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="active", comment="用户状态"
    )
    failed_login_count: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="登录失败次数"
    )
    locked_until: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="账户锁定截止时间"
    )
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, comment="最后登录时间"
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="头像地址"
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
        back_populates="user", cascade="all, delete-orphan"
    )


class AuthSession(Base):
    __tablename__ = "auth_sessions"
    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), nullable=False, comment="用户主键"
    )
    refresh_token_hash: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, comment="刷新令牌哈希"
    )
    device_name: Mapped[str | None] = mapped_column(
        String(255), nullable=True, comment="设备名称"
    )
    ip_address: Mapped[str | None] = mapped_column(
        String(45), nullable=True, comment="IP 地址"
    )
    user_agent: Mapped[str | None] = mapped_column(
        String(500), nullable=True, comment="用户代理"
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, index=True, comment="过期时间"
    )
    revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="0",
        comment="是否已撤销",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
