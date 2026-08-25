import json
from typing import Any

from app.agents.agent_service.pending import make_pending
from app.agents.graph.state import AgentState
from app.agents.risk import classify_automation_operation, classify_scene_execution
from app.agents.tools import WRITE_TOOL_NAMES, WRITE_TOOL_SCHEMAS
from fastapi import HTTPException
from langchain_core.messages import AIMessage, ToolMessage
from pydantic import ValidationError
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

                                   
    if len(write_calls) != 1 or len(last.tool_calls) != 1:
        return _tool_error(
            state,
            last.tool_calls,
            "每轮只能请求一个写操作，且不能混合只读和写操作",
        )

    call = write_calls[0]
    call_id = str(call.get("id", ""))
    tool_name = str(call.get("name", ""))

                                              
    try:
        validated = WRITE_TOOL_SCHEMAS[tool_name].model_validate(call.get("args") or {})
        args = validated.model_dump(exclude_none=True)
    except (KeyError, ValidationError) as exc:
        return _tool_error(state, [call], f"写操作参数校验失败：{exc}")

    try:
        decision = _classify_operation(db, state, tool_name, args)
    except HTTPException as exc:
        return _tool_error(state, [call], str(exc.detail))


    pending = make_pending({
        "approval_id": f"{state['run_id']}:{call_id}",
        "run_id": state["run_id"],
        "session_id": state["context"].session_id,
        "call_id": call_id,
        "tool": tool_name,
        "args": args,
        "risk_level": decision.level,
        "reasons": decision.reasons,
        "preview": decision.preview,
        "resource_version": decision.resource_version,
        "model_name": state.get("model_name", ""),
        "model_id": state.get("model_id"),
    })

    return {
        "pending_approval": pending,
        "approval_decision": (
            {"decision": "approve", "automatic": True}
            if not decision.requires_approval
            else None
        ),
    }


def _tool_error(state: AgentState, calls: list[Any], message: str) -> dict:
    return {
        "messages": [
            ToolMessage(
                content=json.dumps({"ok": False, "error": message}, ensure_ascii=False),
                tool_call_id=str(call.get("id", "")),
                name=str(call.get("name", "")),
            )
            for call in calls
        ],
        "pending_approval": None,
        "approval_decision": None,
        "rounds": state.get("rounds", 0) + 1,
    }


def _classify_operation(
    db: Session,
    state: AgentState,
    tool_name: str,
    args: dict,
):
    """按工具类型分发到对应的风险分类器。"""
    context = state["context"]

    if tool_name == "execute_scene":
        scene_id = str(args.get("scene_id", "")).strip()
        if not scene_id:
            return None
        return classify_scene_execution(db=db, context=context, scene_id=scene_id)

    if tool_name == "create_automation":
        actions = args.get("actions", [])
        return classify_automation_operation(
            db=db,
            context=context,
            operation="create_automation",
            actions=actions,
            args=args,
        )

    if tool_name == "update_automation":
        automation_id = args.get("automation_id")
        if automation_id is None:
            return None
        actions = args.get("actions", [])
        return classify_automation_operation(
            db=db,
            context=context,
            operation="update_automation",
            automation_id=automation_id,
            actions=actions,
            args=args,
        )

    if tool_name == "set_automation_enabled":
        automation_id = args.get("automation_id")
        if automation_id is None:
            return None
        return classify_automation_operation(
            db=db,
            context=context,
            operation="set_automation_enabled",
            automation_id=automation_id,
            args=args,
        )

    if tool_name == "delete_automation":
        automation_id = args.get("automation_id")
        if automation_id is None:
            return None
        return classify_automation_operation(
            db=db,
            context=context,
            operation="delete_automation",
            automation_id=automation_id,
        )

    raise ValueError(f"不支持的写工具：{tool_name}")
