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
    api: Mapped[str] = mapped_column(
        String(40),
        nullable=False,
        server_default="openai-completions",
        comment="API 协议：openai-completions / openai-responses / anthropic-messages / bedrock-converse-stream",
    )
    api_endpoint: Mapped[str] = mapped_column(
        String(200), nullable=False, comment="API 地址"
    )
    api_key: Mapped[str] = mapped_column(Text, nullable=True, comment="API 密钥")
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, comment="模型参数")
    reasoning: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default="0", comment="是否支持思考/推理"
    )
    thinking_level_map: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="思考等级映射 {off/low/medium/...: 供应商取值或 null}"
    )
    context_window: Mapped[int | None] = mapped_column(
        Integer, nullable=True, comment="上下文窗口 tokens"
    )
    cost: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="$/百万tokens {input,output,cacheRead,cacheWrite,tiers?}"
    )
    headers: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="附加请求头"
    )
    compat: Mapped[dict | None] = mapped_column(
        JSON, nullable=True, comment="兼容配置（按 api 协议校验）"
    )
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

    @property
    def has_api_key(self) -> bool:
        """仅暴露密钥是否已配置，绝不序列化密钥内容。"""
        return bool(self.api_key)
