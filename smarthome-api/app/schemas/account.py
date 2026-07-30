from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


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


class AvatarResponse(BaseModel):
    avatar_url: str | None
