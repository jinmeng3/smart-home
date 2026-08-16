from datetime import datetime
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)


class AccountRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    avatar_url: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=50)
    email: EmailStr | None = None

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: str | None) -> str | None:
        """先清理空白，再执行字段长度校验。"""
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_update_field(self) -> "AccountUpdate":
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("更新字段不能为 null")
        return self


class AvatarResponse(BaseModel):
    avatar_url: str | None


class PreferencesSchema(BaseModel):
    model_config = ConfigDict(
        alias_generator=lambda value: (
            value.split("_")[0] + "".join(part.title() for part in value.split("_")[1:])
        ),
        populate_by_name=True,
    )

    def model_dump(self, **kwargs):
        """默认使用别名序列化，确保 camelCase 字段名正确输出。"""
        kwargs.setdefault("by_alias", True)
        return super().model_dump(**kwargs)


class AppearancePreferences(PreferencesSchema):
    theme_mode: Literal["light", "dark", "system"] = "light"
    font_size: Literal["small", "medium", "large"] = "medium"
    animations_enabled: bool = True
    sidebar_collapsed: bool = False
    performance_mode: bool = False


class AIAssistantPreferences(PreferencesSchema):
    detail_level: int = Field(default=70, ge=0, le=100)
    auto_execute_low_risk: bool = True
    confirm_high_risk: bool = True


class NotificationPreferences(PreferencesSchema):
    device_offline: bool = True
    security_alerts: bool = True
    automation_results: bool = True
    quiet_start: str = Field(default="23:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    quiet_end: str = Field(default="07:00", pattern=r"^([01]\d|2[0-3]):[0-5]\d$")


class SecurityPreferences(PreferencesSchema):
    two_factor_enabled: bool = True


class BackupPreferences(PreferencesSchema):
    auto_backup: bool = True


class UserPreferencesWrite(PreferencesSchema):
    appearance: AppearancePreferences = Field(default_factory=AppearancePreferences)
    ai_assistant: AIAssistantPreferences = Field(default_factory=AIAssistantPreferences)
    notifications: NotificationPreferences = Field(
        default_factory=NotificationPreferences
    )
    security: SecurityPreferences = Field(default_factory=SecurityPreferences)
    backup: BackupPreferences = Field(default_factory=BackupPreferences)
