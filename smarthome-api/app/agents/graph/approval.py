import json
from typing import Literal

from app.agents.graph.state import AgentState
from langchain_core.messages import ToolMessage
from langgraph.types import interrupt

Decision = Literal["approve", "reject"]


def approval_interrupt(state: AgentState) -> dict:
    pending = state.get("pending_approval")
    if not pending:
        raise ValueError("待确认操作不存在")

    decision = interrupt(pending)

    value = str(decision.get("decision", ""))
    approval_id = str(decision.get("approval_id", ""))

    if approval_id != pending["approval_id"]:
        raise ValueError("确认请求与当前待处理操作不匹配")

    if value not in {"approve", "reject"}:
        raise ValueError("不支持的确认决定")

    return {
        "approval_decision": {
            "decision": value,
            "automatic": False,
        }
    }



def reject_tool(state: AgentState) -> dict:
    pending = state.get("pending_approval")
    if not pending:
        raise ValueError("待确认操作不存在")

    return {
        "messages": [
            ToolMessage(
                content=json.dumps(
                    {
                        "ok": False,
                        "status": "rejected",
                        "error": "用户拒绝执行该场景",
                    },
                    ensure_ascii=False,
                ),
                tool_call_id=pending["call_id"],
                name=pending["tool"],
            )
        ],
        "pending_approval": None,
        "approval_decision": None,
        "rounds": state.get("rounds", 0) + 1,
    }
