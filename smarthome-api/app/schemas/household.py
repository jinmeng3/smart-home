from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


def normalize_blank(value: str | None) -> str | None:
    if value is None:
        return None

    stripped = value.strip()
    return stripped or None


class HouseholdCreate(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    timezone: str = Field(default="Asia/Shanghai", min_length=1, max_length=64)

    @field_validator("address")
    @classmethod
    def clean_address(cls, value: str | None) -> str | None:
        return normalize_blank(value)


class HouseholdUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=80)
    address: str | None = Field(default=None, max_length=255)
    timezone: str | None = Field(default=None, min_length=1, max_length=64)

    @field_validator("address")
    @classmethod
    def clean_address(cls, value: str | None) -> str | None:
        return normalize_blank(value)


class HouseholdRead(BaseModel):
    id: int
    name: str
    address: str | None
    timezone: str
    created_by: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class HouseholdListItem(HouseholdRead):
    role: str
    member_count: int
