from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AIModel(Base):
    __tablename__ = "ai_models"

    id: Mapped[int] = mapped_column(primary_key=True, comment="主键")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), nullable=False, comment="用户主键"
    )
    name: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, comment="模型名称"
    )
    provider: Mapped[str] = mapped_column(String(50), comment="模型提供商")
    api_endpoint: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="API 地址"
    )
    api_key: Mapped[str] = mapped_column(Text, nullable=True, comment="API 密钥")
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, comment="模型参数")
    temperature: Mapped[float] = mapped_column(
        Float,
        default=0.7,
        server_default="0.7",
        nullable=False,
        comment="采样温度",
    )
    max_tokens: Mapped[int] = mapped_column(
        Integer,
        default=4096,
        server_default="4096",
        nullable=False,
        comment="最大令牌数",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="1",
        comment="是否启用",
    )
    description: Mapped[str | None] = mapped_column(
        Text, nullable=True, comment="模型描述"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="创建时间",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间",
    )
