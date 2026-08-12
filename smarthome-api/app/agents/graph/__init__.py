from collections.abc import Sequence
from functools import partial

from app.agents.audit.recorder import AuditRecorder
from app.agents.graph.nodes import finalize, load_context, model_node
from app.agents.graph.state import AgentState
from app.agents.graph.tool_router import execute_tools, should_continue
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph


def build_graph(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    *,
    audit: AuditRecorder | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
):
    tools_by_name = {tool.name: tool for tool in tools}
    bound_model = model.bind_tools(tools)
    graph = StateGraph(AgentState)  # type: ignore
    graph.add_node("load_context", load_context)
    graph.add_node("model", partial(model_node, model=bound_model))
    graph.add_node(
        "tool",
        partial(execute_tools, tools_by_name=tools_by_name, audit=audit),
    )
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "model")
    graph.add_conditional_edges(
        "model", should_continue, {"tool": "tool", "finalize": "finalize"}
    )
    graph.add_edge("tool", "model")
    graph.add_edge("finalize", END)
    return graph.compile(checkpointer=checkpointer)
