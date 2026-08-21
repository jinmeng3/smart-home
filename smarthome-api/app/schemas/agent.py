from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AgentRunRequest(BaseModel):
    session_id: int = Field(gt=0)
    household_id: int = Field(gt=0)
    household_name: str | None = Field(default=None, deprecated=True)
    model: str | None = None
    message: str = Field(min_length=1, max_length=4000)
    tools_enabled: bool = True

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("消息不能为空")
        return value


class AgentDecisionRequest(BaseModel):
    household_id: int = Field(gt=0)
    approval_id: str = Field(min_length=1, max_length=200)
    decision: Literal["approve", "reject"]


class PendingApprovalRead(BaseModel):
    approval_id: str
    run_id: str
    session_id: int
    call_id: str
    tool: str
    args: dict[str, Any]
    risk_level: str
    reasons: list[str]
    preview: dict[str, Any]
    resource_version: str
