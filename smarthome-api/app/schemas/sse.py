from pydantic import BaseModel, Field


class AgentEvent(BaseModel):
    event_id: str
    run_id: str
    event: str = ""


class RunStarted(AgentEvent):
    event: str = "run_started"
    session_id: int
    household_id: int


class MessageDelta(AgentEvent):
    event: str = "message_delta"
    content: str


class ToolStarted(AgentEvent):
    event: str = "tool_started"
    call_id: str
    tool: str
    summary: str = ""


class ToolCompleted(AgentEvent):
    event: str = "tool_completed"
    call_id: str
    tool: str
    result: str = ""


class ToolFailed(AgentEvent):
    event: str = "tool_failed"
    call_id: str
    tool: str
    code: str = "AGENT_TOOL_EXECUTION_ERROR"
    error: str = ""


class ApprovalRequired(AgentEvent):
    event: str = "approval_required"
    session_id: int
    approval_id: str
    operator: str
    call_id: str = ""
    risk_level: str = ""
    reasons: list[str] = Field(default_factory=list)
    preview: dict = Field(default_factory=dict)


class ExecutionStatus(AgentEvent):
    event: str = "execution_status"
    session_id: int
    operator: str
    status: str
    call_id: str = ""
    execution_id: str | None = None
    message: str = ""


class RunCompleted(AgentEvent):
    event: str = "run_completed"
    session_id: int
    status: str = "completed"
    message_id: int | None = None


class Error(AgentEvent):
    event: str = "error"
    code: str = "AGENT_INTERNAL_ERROR"
    message: str
    retryable: bool = False
