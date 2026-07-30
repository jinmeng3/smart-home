from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Smart Home API"
    database_url: str = "sqlite:///./db/orion_home.db"
    upload_dir: str = "app/uploads"
    max_avatar_size: int = 2 * 1024 * 1024
    allowed_avatar_types: set[str] = {"image/jpeg", "image/png", "image/webp"}
    development_mode: bool = True

    model_config = SettingsConfigDict(env_file=".env", env_prefix="SMART_HOME_")

    @property
    def avatar_dir(self) -> Path:
        return Path(self.upload_dir) / "avatars"


@lru_cache
def get_settings() -> Settings:
    return Settings()
