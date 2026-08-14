from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RiskLevel(StrEnum):
    READ_ONLY = "read_only"
    LOW = "low"
    HIGH = "high"
    UNKNOWN = "unknown"


class RiskDecision(BaseModel):
    level: RiskLevel
    requires_approval: bool
    reasons: list[str] = Field(default_factory=list)
    preview: dict[str, Any]
    resource_version: str
