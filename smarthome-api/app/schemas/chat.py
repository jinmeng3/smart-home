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
    mode: str = "agent"
    model_name: str | None = None
    created_at: datetime
    updated_at: datetime


class SessionModeUpdate(BaseModel):
    mode: Literal["agent", "chat"]


class SessionModelUpdate(BaseModel):
    model_name: str = Field(min_length=1, max_length=100)


class RegenerateRequest(BaseModel):
    target_message_id: int = Field(gt=0)
    model: str | None = None
    household_id: int | None = Field(default=None, gt=0)

    model_config = ConfigDict(extra="allow")
