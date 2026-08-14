from app.agents.graph.state import AgentState
from app.agents.tools import WRITE_TOOL_NAMES
from app.core.config import get_settings
from langchain_core.messages import AIMessage


def should_continue(state: AgentState) -> str:
    settings = get_settings()
    if state.get("rounds", 0) >= settings.agent_max_rounds:
        return "finalize"
    last = state["messages"][-1]
    if not isinstance(last, AIMessage) or not last.tool_calls:
        return "finalize"

    names = {str(call.get("name", "")) for call in last.tool_calls}

    if names & WRITE_TOOL_NAMES:
        return "risk_check"

    return "read_tool"


def route_after_risk(state: AgentState) -> str:
    decision = state.get("approval_decision")
    if decision and decision.get("decision") == "approve":
        return "write_tool"

    return "approval_interrupt"


def route_after_approval(state: AgentState) -> str:
    decision = state.get("approval_decision")
    if decision and decision.get("decision") == "approve":
        return "write_tool"
    return "reject_tool"