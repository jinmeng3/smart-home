from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class AIModelRead(BaseModel):
    id: int
    name: str
    provider: str
    api_endpoint: str
    parameters: dict
    temperature: float
    max_tokens: int
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AIModelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    provider: str = Field(min_length=1, max_length=50)
    api_endpoint: str = Field(min_length=1, max_length=200)
    api_key: str | None = None
    parameters: dict = Field(default_factory=dict)
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, gt=0)
    is_active: bool = True
    description: str | None = None

    @field_validator("name", "provider", "api_endpoint", "api_key", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value


class AIModelUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    provider: str | None = Field(default=None, min_length=1, max_length=50)
    api_endpoint: str | None = Field(default=None, min_length=1, max_length=200)
    api_key: str | None = None
    parameters: dict | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    description: str | None = None

    @field_validator("name", "provider", "api_endpoint", "api_key", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def require_update_field(self) -> "AIModelUpdate":
        if not self.model_fields_set:
            raise ValueError("至少需要提供一个更新字段")
        return self
