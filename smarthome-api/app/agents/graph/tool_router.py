import asyncio
import time

from app.agents.graph.state import AgentState
from app.core.config import get_settings
from langchain_core.messages import AIMessage, ToolMessage


def should_continue(state: AgentState) -> str:
    settings = get_settings()
    if state.get("rounds", 0) >= settings.agent_max_rounds:
        return "finalize"
    last = state["messages"][-1]
    if isinstance(last, AIMessage) and last.tool_calls:
        return "tool"
    return "finalize"


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

        if tool is None:
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
        tool_messages.append(
            ToolMessage(
                content=str(content)[: settings.tool_result_max_length],
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
