from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AIModelRead(BaseModel):
    name: str
    provider: str
    api_endpoint: str
    temperature: float
    max_tokens: int
    is_active: bool
    description: str | None
    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AIModelCreate(BaseModel):
    name: str
    provider: str
    api_endpoint: str
    api_key: str | None = None
    temperature: float = Field(default=0.7, ge=0, le=2)
    max_tokens: int = Field(default=4096, gt=0)
    is_active: bool = True
    description: str | None = None


class AIModelUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    api_endpoint: str | None = None
    api_key: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    max_tokens: int | None = Field(default=None, gt=0)
    is_active: bool | None = None
    description: str | None = None
