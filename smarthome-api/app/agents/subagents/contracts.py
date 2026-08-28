from pydantic import BaseModel, Field


class SubAgentInput(BaseModel):
    """一次子 Agent 调用所需的全部输入。

    ``household_id`` 沿用 ``AgentContext.household_id`` 的 ``int`` 类型，
    通过透传主 ``AgentContext`` 保证多家庭隔离。
    """

    household_id: int
    session_id: int
    user_id: int
    domain: str
    task: str
    session_summary: str = ""
    shared_context: dict = Field(default_factory=dict)
    max_tool_calls: int = Field(default=5, ge=1)
    timeout_seconds: float = Field(default=8.0, gt=0)


class SubAgentOutput(BaseModel):
    """子 Agent 的返回结果。

    ``write_proposals`` 仅 scene / automation 等写提案型子 Agent 使用，
    结构严格对应现有 ``WRITE_TOOL_NAMES`` 中写工具的一次调用参数。
    """

    domain: str
    response_text: str
    structured_data: dict = Field(default_factory=dict)
    write_proposals: list[dict] = Field(default_factory=list)
    fallback_needed: bool = False
    error: str | None = None
