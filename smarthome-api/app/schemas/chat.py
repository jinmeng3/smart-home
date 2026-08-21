from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChatCompletionMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str = Field(min_length=1)


class ChatCompletionRequest(BaseModel):
    model: str | None = None
    messages: list[ChatCompletionMessage] = Field(min_length=1)
    session_id: int | None = Field(default=None, gt=0)
    stream: bool = False

    model_config = ConfigDict(extra="allow")


class ChatSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ChatMessageRead(ChatSchema):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime


class ChatSessionRead(ChatSchema):
    id: int
    title: str
    household_id: int | None = None
    created_at: datetime
    updated_at: datetime
