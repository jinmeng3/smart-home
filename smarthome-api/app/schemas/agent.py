from pydantic import BaseModel, Field, field_validator


class AgentRunRequest(BaseModel):
    session_id: int
    household_id: int
    household_name: str | None = None
    model: str | None = None
    message: str = Field(min_length=1, max_length=4000)

    @field_validator("message")
    @classmethod
    def strip_message(cls, v: str) -> str:
        return v.strip()
