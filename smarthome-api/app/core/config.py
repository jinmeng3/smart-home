from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Home API"
    development_mode: bool = True

    database_url: str = "sqlite:///./db/orion_home.db"

    jwt_secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_seconds: int = 3600
    max_failed_login_attempts: int = Field(default=5, ge=1, le=20)
    login_lock_seconds: int = Field(default=900, ge=60, le=86400)

    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    supported_ai_providers: list[str] = Field(
        default_factory=lambda: ["openai", "deepseek"]
    )
    max_cache_size: int = Field(default=100, ge=1)
    model_timeout_seconds: float = Field(default=30.0, gt=0, le=300)
    model_max_retries: int = Field(default=2, ge=0, le=5)

    @field_validator("supported_ai_providers", mode="before")
    @classmethod
    def split_providers(cls, value):
        """兼容逗号分隔与 JSON 数组两种 env 写法：
        SUPPORTED_AI_PROVIDERS=openai,deepseek
        SUPPORTED_AI_PROVIDERS=["openai","deepseek"]
        """
        if not isinstance(value, str):
            return value
        stripped = value.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            import json as _json

            try:
                parsed = _json.loads(stripped)
                if isinstance(parsed, list):
                    return parsed
            except ValueError:
                pass
        return [v.strip() for v in value.split(",") if v.strip()]

    upload_dir: str = "app/uploads"
    max_avatar_size: int = 2 * 1024 * 1024
    allowed_avatar_types: set[str] = Field(
        default_factory=lambda: {"image/jpeg", "image/png", "image/webp"}
    )
    max_device_image_size: int = 5 * 1024 * 1024
    allowed_device_image_types: set[str] = Field(
        default_factory=lambda: {"image/jpeg", "image/png", "image/webp"}
    )

    audit_dir: str = "agent_audit"

    agent_rate_limit_per_minute: int = Field(
        default=10, ge=1, le=120, description="每分钟每个用户最大 agent 请求数"
    )
    agent_daily_budget_tokens: int = Field(
        default=500000, ge=0, description="每个用户每日最大 token 消耗"
    )
    agent_lease_ttl_seconds: int = Field(
        default=600,
        ge=30,
        le=3600,
        description="会话运行租约 TTL；进程崩溃后超过该时长允许新运行接管。"
        "注意：长时间运行的合法 Agent 调用不应超过此值，否则租约可能被窃取。",
    )
    approval_ttl_seconds: int = Field(
        default=1800,
        ge=60,
        le=86400,
        description="待审批操作有效期；过期后拒绝审批并要求重新预览与确认",
    )
    checkpointer_database_url: str | None = Field(
        default=None, description="SQLite checkpoint 文件路径覆盖（默认从 DATABASE_URL 推导）"
    )
    api_key_encryption_secret: str | None = Field(
        default=None, description="API Key 独立加密密钥；生产环境必须配置"
    )
    production_mode: bool = Field(
        default=False, description="生产模式，启用加密、限流等"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    agent_max_rounds: int = Field(default=6, ge=1)
    tool_timeout_seconds: float = Field(default=15.0, gt=0)
    tool_result_max_length: int = Field(default=4000, ge=1)
    tool_error_prefix: str = "[tool_error] "

    graph_recursion_limit: int = Field(default=10, ge=1)

    agent_tool_result_max_length: int = Field(default=100, ge=1)

    # ── 漏斗式分层路由（funnel-routing-architecture）──
    funnel_enabled: bool = Field(
        default=True,
        description="是否启用漏斗式分层路由（规则层前置拦截）",
    )
    funnel_rule_confidence_high: float = Field(
        default=0.95, ge=0.0, le=1.0,
        description="规则层置信度 >= 该值时直接本地执行，跳过 LLM",
    )
    funnel_rule_confidence_low: float = Field(
        default=0.8, ge=0.0, le=1.0,
        description="规则层置信度低于该值时丢弃，交给上层（上下文层 / 兜底层）",
    )
    funnel_rule_max_duration_ms: int = Field(
        default=50, ge=1, le=1000,
        description="规则层解析硬性预算（毫秒），超时的回退到上下文层",
    )
    funnel_alias_hot_reload: bool = Field(
        default=True,
        description="别名库变更时是否即时刷新（False 则需重启进程）",
    )
    funnel_context_enabled: bool = Field(
        default=True,
        description="是否启用漏斗第二层（上下文层）多轮 / 指代消解",
    )

    # ── 上下文压缩 / 会话树 ──
    compaction_enabled: bool = True
    compaction_reserve_tokens: int = Field(default=16384, ge=1)
    compaction_keep_recent_tokens: int = Field(default=20000, ge=1)
    compaction_branch_summary_max_tokens: int = Field(default=2048, ge=1)
    compaction_tool_result_max_chars: int = Field(default=2000, ge=1)
    compaction_retry_attempts: int = Field(default=0, ge=0)
    compaction_max_tokens: int | None = Field(default=None, gt=0)
    session_tree_context_window: int = Field(default=200000, gt=0)

    def compaction_settings(self):
        """把 ``.env`` 中的压缩配置构建为 ``session_tree`` 的 ``CompactionSettings``。"""
        from app.session_tree.session.types import CompactionSettings

        return CompactionSettings(
            enabled=self.compaction_enabled,
            reserve_tokens=self.compaction_reserve_tokens,
            keep_recent_tokens=self.compaction_keep_recent_tokens,
        )

    @property
    def avatar_dir(self) -> Path:
        return Path(self.upload_dir) / "avatars"

    @property
    def device_image_dir(self) -> Path:
        return Path(self.upload_dir) / "devices"

    @property
    def audit_path(self) -> Path:
        return Path(self.audit_dir)


@lru_cache
def get_settings() -> Settings:
    return Settings()
