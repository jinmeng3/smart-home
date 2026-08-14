from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


class AgentRunRequest(BaseModel):
    session_id: int
    household_id: int
    household_name: str
    model: str | None = None
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, value: str) -> str:
        return value.strip()


class AgentDecisionRequest(BaseModel):
    household_id: int
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