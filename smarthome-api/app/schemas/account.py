from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


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


class AvatarResponse(BaseModel):
    avatar_url: str | None
