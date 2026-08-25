from typing import Any

from app.agents.context import AgentContext
from app.agents.errors import AgentContextError, AgentModelEmptyResponseError
from app.agents.graph.state import AgentState
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable


def load_context(state: AgentState) -> dict:
    if not isinstance(state.get("context"), AgentContext):
        raise AgentContextError("Agent 上下文缺失或非法")
    return {}


async def model_node(
    state: AgentState, model: Runnable[Any, AIMessage]
) -> dict:
    chunks = []
    async for chunk in model.astream(state["messages"]):
        chunks.append(chunk)
    if not chunks:
        raise AgentModelEmptyResponseError(
            "模型返回空流响应，请检查模型配置或 API 连接"
        )
    response = chunks[0]
    for chunk in chunks[1:]:
        response += chunk
    return {"messages": [response]}


def finalize(state: AgentState) -> dict:
    return {}
