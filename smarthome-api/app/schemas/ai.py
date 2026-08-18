from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

ApiProtocol = Literal[
    "openai-completions",
    "openai-responses",
    "azure-openai-responses",
    "openai-codex-responses",
    "anthropic-messages",
    "bedrock-converse-stream",
]


class AIModelRead(BaseModel):
    id: int
    name: str
    provider: str
    api: str = "openai-completions"
    api_endpoint: str
    parameters: dict
    compat: dict | None = None
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
    api: ApiProtocol = "openai-completions"

    api_endpoint: str = Field(min_length=1, max_length=200)
    api_key: str | None = None
    parameters: dict = Field(default_factory=dict)

    reasoning: bool = False
    thinking_level_map: dict | None = None
    context_window: int | None = None
    max_tokens: int = Field(default=4096, gt=0)
    cost: dict | None = None
    headers: dict | None = None
    compat: dict | None = None
    is_active: bool = True
    description: str | None = None

    @field_validator("name", "provider", "api_endpoint", "api_key", mode="before")
    @classmethod
    def strip_text(cls, value: str | None) -> str | None:
        return value.strip() if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_protocol_compat(self) -> "AIModelCreate":
        if self.compat is not None:
            validator = PROTOCOL_COMPAT_VALIDATORS.get(self.api)
            if validator is None:
                raise ValueError(f"不支持的 API 协议: {self.api}")
            self.compat = validator.model_validate(self.compat).model_dump()
        return self


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


class ModelCostRates(BaseModel):
    input: float
    output: float
    cache_read: float = 0
    cache_write: float = 0


class ModelCostTier(ModelCostRates):
    input_token_above: int


class ModelCost(ModelCostRates):
    tiers: list[ModelCostTier] | None = None


class OpenAICompletionsCompat(BaseModel):
    force_json_mode: bool | None = None
    session_affinity: bool | None = None


class OpenAIResponsesCompat(BaseModel):
    force_json_mode: bool | None = None
    include_reasoning: bool | None = None


class AnthropicMessagesCompat(BaseModel):
    force_json_mode: bool | None = None
    cache_control: bool | None = None


class BedrockCompat(BaseModel):
    region: str | None = None


PROTOCOL_COMPAT_VALIDATORS: dict[str, type[BaseModel]] = {
    "openai-completions": OpenAICompletionsCompat,
    "openai-responses": OpenAIResponsesCompat,
    "azure-openai-responses": OpenAIResponsesCompat,
    "openai-codex-responses": OpenAIResponsesCompat,
    "anthropic-messages": AnthropicMessagesCompat,
    "bedrock-converse-stream": BedrockCompat,
}
