from collections.abc import Sequence
from functools import partial
from typing import Any, cast

from app.agents.audit.recorder import AuditRecorder
from app.agents.graph.approval import (
    approval_interrupt,
    reject_tool,
)
from app.agents.graph.execute import execute_tools, execute_write_tool
from app.agents.graph.nodes import finalize, load_context, model_node
from app.agents.graph.risk_node import risk_check
from app.agents.graph.state import AgentState
from app.agents.graph.tool_router import (
    route_after_approval,
    route_after_risk,
    should_continue,
)
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import BaseTool
from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph
from sqlalchemy.orm import Session


def build_graph(
    model: BaseChatModel,
    tools: Sequence[BaseTool],
    db: Session,
    *,
    audit: AuditRecorder | None = None,
    checkpointer: BaseCheckpointSaver | None = None,
    tools_enabled: bool = True,
):


    active_tools = tools if tools_enabled else []
    tools_by_name = {tool.name: tool for tool in active_tools}
    bound_model = model.bind_tools(active_tools)

    graph = StateGraph(cast(Any, AgentState))

    graph.add_node("load_context", load_context)
    graph.add_node("model", partial(model_node, model=bound_model))
    graph.add_node(
        "read_tool",
        partial(execute_tools, tools_by_name=tools_by_name, audit=audit),
    )
    graph.add_node("risk_check", partial(risk_check, db=db))
    graph.add_node("approval_interrupt", approval_interrupt)
    graph.add_node("write_tool", partial(execute_write_tool, db=db))
    graph.add_node("reject_tool", reject_tool)
    graph.add_node("finalize", finalize)

    graph.add_edge(START, "load_context")
    graph.add_edge("load_context", "model")

    graph.add_conditional_edges(
        "model",
        should_continue,
        {
            "read_tool": "read_tool",
            "risk_check": "risk_check",
            "finalize": "finalize",
        },
    )

    graph.add_edge("read_tool", "model")

    graph.add_conditional_edges(
        "risk_check",
        route_after_risk,
        {
            "model": "model",
            "write_tool": "write_tool",
            "approval_interrupt": "approval_interrupt",
        },
    )

    graph.add_conditional_edges(
        "approval_interrupt",
        route_after_approval,
        {
            "write_tool": "write_tool",
            "reject_tool": "reject_tool",
        },
    )

    graph.add_edge("write_tool", "model")
    graph.add_edge("reject_tool", "model")
    graph.add_edge("finalize", END)

    return graph.compile(checkpointer=checkpointer)
