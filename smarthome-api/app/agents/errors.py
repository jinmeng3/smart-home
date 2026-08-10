class AgentError(Exception):
    code = "AGENT_INTERNAL_ERROR"
    http_status = 500
    retryable = False

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        http_status: int | None = None,
        retryable: bool | None = None,
    ):
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
