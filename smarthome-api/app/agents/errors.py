class AgentError(Exception):
    """Agent 业务异常基类；子类通过覆盖 ``code``/``http_status``/``retryable`` 声明语义。"""

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
    """``ModelsRegistry.resolve``：provider 不在 ``supported_ai_providers`` 之内。"""

    code = "UNSUPPORTED_MODEL_PROVIDER"
    http_status = 400


class ModelCredentialsMissing(AgentError):
    """``ModelsRegistry.apply_auth``：API Key 或 Base URL 缺失/解密后为空。"""

    code = "MODEL_CREDENTIALS_MISSING"
    http_status = 400


class ModelToolCallingUnsupported(AgentError):
    """模型工厂能力探测：所选模型不支持 function calling，但 Agent 流程必需。"""

    code = "MODEL_TOOL_CALLING_UNSUPPORTED"
    http_status = 400


class ModelProtocolMismatch(AgentError):
    """``ModelsRegistry.resolve``：provider 存在但 ``api`` 不在 ``supported_api`` 内。"""

    code = "MODEL_PROTOCOL_MISMATCH"
    http_status = 400
    retryable = False


class AgentContextError(AgentError):
    """``AgentContext.from_request``：家庭上下文解析失败（未登录/家庭越权/token 无效）。"""

    code = "AGENT_CONTEXT_UNAUTHORIZED"
    http_status = 403
    retryable = False


class AgentSessionNotFound(AgentError):
    """runner/resumer：会话 ID 不存在或不属于当前家庭。"""

    code = "AGENT_SESSION_NOT_FOUND"
    http_status = 404


class AgentModelNotFound(AgentError):
    """会话绑定模型加载：模型记录已被删除。"""

    code = "AGENT_MODEL_NOT_FOUND"
    http_status = 404


class AgentModelInactive(AgentError):
    """模型工厂闸门：模型存在但 ``is_active=False``。"""

    code = "AGENT_MODEL_INACTIVE"
    http_status = 400


class AgentCheckpointerError(AgentError):
    """checkpointer 读写失败：SQLite 锁 / 磁盘满 / 连接断。"""

    code = "AGENT_CHECKPOINTER_ERROR"
    http_status = 500


class AgentToolExecutionError(AgentError):
    """``app.agents.tools.*`` ``invoke`` 包装层：工具执行阶段抛非预期异常。"""

    code = "AGENT_TOOL_EXECUTION_ERROR"
    http_status = 500


class AgentRateLimitError(AgentError):
    """runner 入口限流：每分钟请求超 ``agent_rate_limit_per_minute``。"""

    code = "AGENT_RATE_LIMIT_EXCEEDED"
    http_status = 429


class AgentBudgetExceededError(AgentError):
    """runner 内的 token 计数器：当日用量超 ``agent_daily_budget_tokens``。"""

    code = "AGENT_BUDGET_EXCEEDED"
    http_status = 429


class AgentApprovalExpiredError(AgentError):
    """审批入口：待审批操作超过 ``approval_ttl_seconds``，需重新预览。"""

    code = "AGENT_APPROVAL_EXPIRED"
    http_status = 409


class AgentModelEmptyResponseError(AgentError):
    """模型流式响应为空（content/usage 缺失、stream 中断）；``retryable=True``，重发大概率成功。"""

    code = "AGENT_MODEL_EMPTY_RESPONSE"
    http_status = 502
    retryable = True


class AgentDeviceReadbackError(AgentError):
    """执行类工具的写后回读：设备实际状态与预期不一致（离线/丢命令/上报延迟）。"""

    code = "AGENT_DEVICE_READBACK_FAILED"
    http_status = 500
