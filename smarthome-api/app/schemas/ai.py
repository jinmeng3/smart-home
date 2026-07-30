from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AIModelRead(BaseModel):
    name: str
    provider: str
    is_active: bool
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AIModelUpdate(BaseModel):
    name: str | None = None
    provider: str | None = None
    is_active: bool | None = None
    description: str | None = None
