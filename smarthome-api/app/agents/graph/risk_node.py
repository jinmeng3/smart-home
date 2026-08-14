import json

from app.agents.graph.state import AgentState
from app.agents.risk import classify_scene_execution
from app.agents.tools import WRITE_TOOL_NAMES
from langchain_core.messages import AIMessage, ToolMessage
from sqlalchemy.orm import Session


def risk_check(state: AgentState, db: Session) -> dict:
    last = state["messages"][-1]
    if not isinstance(last, AIMessage):
        raise TypeError("risk_check只能处理模型工具调用")

    write_calls = [
        call
        for call in last.tool_calls
        if str(call.get("name", "")) in WRITE_TOOL_NAMES
    ]

    # 第一版限制每轮只能执行一个写操作，避免部分成功和确认语义歧义。
    if len(write_calls) != 1 or len(last.tool_calls) != 1:
        messages = [
            ToolMessage(
                content=json.dumps(
                    {
                        "ok": False,
                        "error": "每轮只能请求一个写操作，且不能混合只读和写操作",
                    },
                    ensure_ascii=False,
                ),
                tool_call_id=str(call.get("id", "")),
                name=str(call.get("name", "")),
            )
            for call in write_calls
        ]
        return {
            "messages": messages,
            "pending_approval": None,
            "rounds": state.get("rounds", 0) + 1,
        }

    call = write_calls[0]
    call_id = str(call.get("id", ""))
    tool_name = str(call.get("name", ""))
    args = call.get("args") or {}

    if tool_name != "execute_scene":
        raise ValueError(f"不支持的写工具：{tool_name}")

    scene_id = str(args.get("scene_id", "")).strip()
    if not scene_id:
        return {
            "messages": [
                ToolMessage(
                    content=json.dumps(
                        {"ok": False, "error": "缺少scene_id"},
                        ensure_ascii=False,
                    ),
                    tool_call_id=call_id,
                    name=tool_name,
                )
            ],
            "pending_approval": None,
        }

    decision = classify_scene_execution(
        db=db,
        context=state["context"],
        scene_id=scene_id,
    )

    pending = {
        "approval_id": f"{state['run_id']}:{call_id}",
        "run_id": state["run_id"],
        "session_id": state["context"].session_id,
        "call_id": call_id,
        "tool": tool_name,
        "args": {"scene_id": scene_id},
        "risk_level": decision.level,
        "reasons": decision.reasons,
        "preview": decision.preview,
        "resource_version": decision.resource_version,
    }

    return {
        "pending_approval": pending,
        "approval_decision": (
            {"decision": "approve", "automatic": True}
            if not decision.requires_approval
            else None
        ),
    }



