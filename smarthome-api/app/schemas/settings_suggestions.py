from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SettingsSectionId = Literal[
    "account",
    "appearance",
    "ai",
    "homeAssistant",
    "notifications",
    "security",
    "backup",
]


class AiSuggestionItem(BaseModel):
    id: str = Field(min_length=1, max_length=64)
    target: SettingsSectionId
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(min_length=1, max_length=300)


class AiSuggestionsRead(BaseModel):
    suggestions: list[AiSuggestionItem] = Field(default_factory=list)
    cached: bool = False

    model_config = ConfigDict(from_attributes=True)
