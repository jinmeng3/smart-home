from typing import Annotated, Any, TypedDict

from app.agents.context import AgentContext
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict, total=False):
    messages: Annotated[list[BaseMessage], add_messages]
    context: AgentContext
    run_id: str
    rounds: int  # 已执行的工具轮数，防止死循环
    pending_approval: dict[str, Any] | None
    approval_decision: dict[str, Any] | None
