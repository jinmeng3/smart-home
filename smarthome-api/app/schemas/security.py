from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SecurityDeviceRead(BaseModel):
    id: int
    device_name: str
    location: str
    last_active_at: datetime
    trusted: bool
    is_current: bool

    model_config = ConfigDict(from_attributes=True)


class SecurityDeviceTrustUpdate(BaseModel):
    trusted: bool


class SecurityLogRead(BaseModel):
    id: int
    title: str
    detail: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityLogCreate(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    detail: str = Field(min_length=1, max_length=1024)


class SecurityMetaRead(BaseModel):
    password_updated_at: datetime | None = None
    devices: list[SecurityDeviceRead] = Field(default_factory=list)
    logs: list[SecurityLogRead] = Field(default_factory=list)