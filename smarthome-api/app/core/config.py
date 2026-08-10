from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 应用
    app_name: str = "Smart Home API"
    development_mode: bool = True

    # 数据库
    database_url: str = "sqlite:///./db/orion_home.db"

    # 身份认证
    jwt_secret_key: str
    access_token_expire_seconds: int = 3600
    max_failed_login_attempts: int = Field(default=5, ge=1, le=20)
    login_lock_seconds: int = Field(default=900, ge=60, le=86400)

    # 跨域资源共享
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    # 模型
    supported_ai_providers: list[str] = Field(
        default_factory=lambda: ["openai", "anthropic", "cohere", "gemini", "deepseek"]
    )
    max_cache_size: int = Field(default=100, ge=1)

    # 文件上传
    upload_dir: str = "app/uploads"
    max_avatar_size: int = 2 * 1024 * 1024
    allowed_avatar_types: set[str] = Field(
        default_factory=lambda: {"image/jpeg", "image/png", "image/webp"}
    )
    max_device_image_size: int = 5 * 1024 * 1024
    allowed_device_image_types: set[str] = Field(
        default_factory=lambda: {"image/jpeg", "image/png", "image/webp"}
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def avatar_dir(self) -> Path:
        return Path(self.upload_dir) / "avatars"

    @property
    def device_image_dir(self) -> Path:
        return Path(self.upload_dir) / "devices"




@lru_cache
def get_settings() -> Settings:
    return Settings()
