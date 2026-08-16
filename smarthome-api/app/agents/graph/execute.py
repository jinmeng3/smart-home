import asyncio
import json
import time

from app.agents.graph.state import AgentState
from app.agents.tools import WRITE_TOOL_NAMES
from app.agents.tools.execute.automations import (
    create_automation_operation,
    delete_automation_operation,
    set_automation_enabled_operation,
    update_automation_operation,
)
from app.agents.tools.execute.scenes import execute_scene_operation
from app.core.config import get_settings
from langchain_core.messages import ToolMessage
from sqlalchemy.orm import Session


async def execute_tools(state, tools_by_name, audit=None) -> dict:
    settings = get_settings()
    error_prefix = settings.tool_error_prefix
    last = state["messages"][-1]
    tool_messages = []
    for call in last.tool_calls:
        call_id = str(call.get("id", ""))
        name = str(call.get("name", ""))
        args = call.get("args") or {}
        tool = tools_by_name.get(name)
        started = time.perf_counter()

        if name in WRITE_TOOL_NAMES:
            content = f"{error_prefix}工具 {name} 是写操作工具，需经过风险评估和用户确认后才能执行"
            ok = False
        elif tool is None:
            content = f"{error_prefix}工具 {name} 不存在"
            ok = False
        else:
            try:
                async with asyncio.timeout(settings.tool_timeout_seconds):
                    content = await tool.ainvoke(args)
                ok = True
            except TimeoutError:
                content = f"{error_prefix}工具 {name} 执行超时"
                ok = False
            except asyncio.CancelledError:
                raise
            except Exception as e:  # noqa: BLE001
                content = f"{error_prefix}工具 {name} 执行异常: {e!s}"
                ok = False

        duration_ms = int((time.perf_counter() - started) * 1000)
        payload = (
            {"ok": True, "data": content}
            if ok
            else {"ok": False, "error": str(content).removeprefix(error_prefix)}
        )
        serialized = json.dumps(payload, ensure_ascii=False, default=str)
        tool_messages.append(
            ToolMessage(
                content=serialized[: settings.tool_result_max_length],
                tool_call_id=call_id,
            )
        )
        if audit is not None:
            audit.record_tool_call(
                run_id=state.get("run_id", ""),
                tool=name,
                call_id=call_id,
                args=args,
                result=content,
                ok=ok,
                duration_ms=duration_ms,
            )

    return {"messages": tool_messages, "rounds": state.get("rounds", 0) + 1}


def execute_write_tool(state: AgentState, db: Session) -> dict:
    pending = state.get("pending_approval")
    decision = state.get("approval_decision")

    if not pending or decision is None:
        raise ValueError("写操作缺少确认上下文")

    if decision.get("decision") != "approve":
        raise ValueError("写操作尚未获得批准")

    context = state["context"]
    tool_name = pending["tool"]
    args = pending["args"]

    # 按工具类型分发到 tools/execute/ 中的实际执行函数
    result = _dispatch_operation(db, context, tool_name, args, pending)

    return {
        "messages": [
            ToolMessage(
                content=json.dumps(result, ensure_ascii=False),
                tool_call_id=pending["call_id"],
                name=pending["tool"],
            )
        ],
        "pending_approval": None,
        "approval_decision": None,
        "rounds": state.get("rounds", 0) + 1,
    }


def _dispatch_operation(db, context, tool_name: str, args: dict, pending: dict) -> dict:
    """按工具类型分发到 agents/tools/execute/ 中的执行函数。"""
    if tool_name == "execute_scene":
        return execute_scene_operation(db, context, args, pending)

    if tool_name == "create_automation":
        return create_automation_operation(db, context, args)

    if tool_name == "update_automation":
        return update_automation_operation(db, context, args)

    if tool_name == "set_automation_enabled":
        return set_automation_enabled_operation(db, context, args)

    if tool_name == "delete_automation":
        return delete_automation_operation(db, context, args)

    return {
        "ok": False,
        "status": "failed",
        "code": "AGENT_UNKNOWN_TOOL",
        "error": f"不支持的写操作工具：{tool_name}",
    }
