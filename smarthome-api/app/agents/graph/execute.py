import asyncio
import json
import time

from app.agents.graph.state import AgentState
from app.agents.risk import classify_scene_execution
from app.agents.tools import WRITE_TOOL_NAMES
from app.core.config import get_settings
from app.services.scene import run_scene_service
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
    scene_id = pending["args"]["scene_id"]

    # 执行前重新读取资源并重新分类，防止确认后场景被修改。
    current = classify_scene_execution(
        db=db,
        context=context,
        scene_id=scene_id,
    )

    if current.resource_version != pending["resource_version"]:
        result = {
            "ok": False,
            "status": "failed",
            "code": "AGENT_APPROVAL_STALE",
            "error": "场景在确认后已发生变化，请重新预览并确认",
        }
    elif current.level != pending["risk_level"]:
        result = {
            "ok": False,
            "status": "failed",
            "code": "AGENT_RISK_CHANGED",
            "error": "场景风险等级已变化，请重新预览并确认",
        }
    else:
        execution = run_scene_service(
            db=db,
            household_id=context.household_id,
            scene_id=scene_id,
            confirm_high_risk=True,
            source="agent",
            idempotency_key=pending["approval_id"],
        )
        result = {
            "ok": True,
            # 当前没有真实设备状态回读，只能表达为已提交。
            "status": "submitted",
            "execution_id": execution.execution_id,
            "scene_id": execution.scene_id,
            "message": "场景已提交到业务执行层，尚未完成设备状态回读验证",
        }

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