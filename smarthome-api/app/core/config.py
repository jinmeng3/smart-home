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

    # 跨域资源共享
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
        ]
    )

    # 文件上传
    upload_dir: str = "app/uploads"
    max_avatar_size: int = 2 * 1024 * 1024
    allowed_avatar_types: set[str] = Field(
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
