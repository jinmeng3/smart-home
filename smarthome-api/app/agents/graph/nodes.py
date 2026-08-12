from typing import Any

from app.agents.context import AgentContext
from app.agents.errors import AgentContextError
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
    response = chunks[0]
    for chunk in chunks[1:]:
        response += chunk
    return {"messages": [response]}


def finalize(state: AgentState) -> dict:
    return {}
