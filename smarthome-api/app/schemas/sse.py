from pydantic import BaseModel


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
    operator: str
    preview: str = ""
    approval_id: str = ""


class ExecutionStatus(AgentEvent):
    event: str = "execution_approved"
    session_id: int
    operator: str
    status: str
    message: str = ""


class RunCompleted(AgentEvent):
    event: str = "run_completed"
    session_id: int
    status: str = "completed"


class Error(AgentEvent):
    event: str = "error"
    code: str = "AGENT_INTERNAL_ERROR"
    message: str
    retryable: bool = False
