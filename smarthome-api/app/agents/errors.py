class AgentError(Exception):
    code = "AGENT_INTERNAL_ERROR"
    http_status = 500
    retryable = False

    def __init__(self, message, *, code=None, http_status=None, retryable=None):
        super().__init__(message)
        if code is not None:
            self.code = code
        if http_status is not None:
            self.http_status = http_status
        if retryable is not None:
            self.retryable = retryable


class UnsupportedModelProvider(AgentError):
    code = "UNSUPPORTED_MODEL_PROVIDER"
    http_status = 400


class ModelCredentialsMissing(AgentError):
    code = "MODEL_CREDENTIALS_MISSING"
    http_status = 400


class ModelToolCallingUnsupported(AgentError):
    code = "MODEL_TOOL_CALLING_UNSUPPORTED"
    http_status = 400


class ModelProtocolMismatch(AgentError):
    code = "MODEL_PROTOCOL_MISMATCH"
    http_status = 400
    retryable = False


class AgentContextError(AgentError):
    code = "AGENT_CONTEXT_UNAUTHORIZED"
    http_status = 403
    retryable = False


class AgentSessionNotFound(AgentError):
    code = "AGENT_SESSION_NOT_FOUND"
    http_status = 404


class AgentModelNotFound(AgentError):
    code = "AGENT_MODEL_NOT_FOUND"
    http_status = 404


class AgentModelInactive(AgentError):
    code = "AGENT_MODEL_INACTIVE"
    http_status = 400


class AgentCheckpointerError(AgentError):
    code = "AGENT_CHECKPOINTER_ERROR"
    http_status = 500


class AgentToolExecutionError(AgentError):
    code = "AGENT_TOOL_EXECUTION_ERROR"
    http_status = 500


class AgentRateLimitError(AgentError):
    code = "AGENT_RATE_LIMIT_EXCEEDED"
    http_status = 429


class AgentBudgetExceededError(AgentError):
    code = "AGENT_BUDGET_EXCEEDED"
    http_status = 429


class AgentDeviceReadbackError(AgentError):
    code = "AGENT_DEVICE_READBACK_FAILED"
    http_status = 500
