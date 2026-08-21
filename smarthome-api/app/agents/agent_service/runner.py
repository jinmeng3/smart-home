import asyncio
from collections.abc import AsyncGenerator
from typing import Any, cast
from uuid import uuid4

from app.agents.audit.recorder import AuditRecorder, get_audit_recorder
from app.agents.checkpointer import get_checkpointer
from app.agents.context import AgentContext
from app.agents.errors import AgentError
from app.agents.events.sse import encode_sse_event
from app.agents.events.stream_tracker import StreamTracker
from app.agents.graph import build_graph
from app.agents.prompts import system_prompt
from app.agents.rate_limiter import check_daily_budget, check_rate_limit, store_usage
from app.agents.redaction import redact_text
from app.agents.tools import get_household_tools
from app.api.deps import get_model_cache
from app.core.config import get_settings
from app.models.ai import AIModel
from app.models.chat import ChatMessage
from app.schemas.sse import (
    ApprovalRequired,
    Error,
    RunCompleted,
    RunStarted,
)
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session


async def _create_graph_runner(
    context: AgentContext, db: Session, model_config: AIModel
) -> tuple[CompiledStateGraph, AuditRecorder]:
    model = get_model_cache().get(model_config)
    tools = get_household_tools(context, db)
    audit = get_audit_recorder()
    graph = build_graph(
        model=model,
        tools=tools,
        db=db,
        audit=audit,
        checkpointer=await get_checkpointer(),
        tools_enabled=context.tools_enabled,
    )
    return graph, audit


def _init_state(
    context: AgentContext,
    household_name: str,
    message: str,
    run_id: str,
    db: Session,
) -> dict[str, Any]:
    sys_prompt = system_prompt(context, household_name, db)
    return {
        "messages": [SystemMessage(content=sys_prompt), HumanMessage(content=message)],
        "context": context,
        "run_id": run_id,
        "rounds": 0,
    }


async def run_agent(
    context: AgentContext,
    household_name: str,
    message: str,
    model_config: AIModel,
    db: Session,
) -> AsyncGenerator[str, None]:
    run_id = f"run-{uuid4().hex}"

    try:
        check_rate_limit(context.user_id)
        check_daily_budget(db, context.user_id)
        graph, audit = await _create_graph_runner(context, db, model_config)
    except AgentError as exc:
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-setup-error",
                run_id=run_id,
                code=exc.code,
                message=redact_text(str(exc)),
                retryable=exc.retryable,
            )
        )
        return
    except Exception:  # noqa: BLE001  # 初始化失败归为一类错误事件返回
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-setup-error",
                run_id=run_id,
                message="Agent 初始化失败，请检查服务配置",
                retryable=False,
            )
        )
        return

    track = StreamTracker(run_id)
    yield encode_sse_event(
        RunStarted(
            event_id=f"{run_id}-start",
            run_id=run_id,
            session_id=context.session_id,
            household_id=context.household_id,
        )
    )

    db.add(ChatMessage(session_id=context.session_id, role="user", content=message))
    db.commit()

    audit.record_run_start(context, run_id)

    initial = _init_state(context, household_name, message, run_id, db)
    thread_id = (
        f"user:{context.user_id}:household:{context.household_id}:"
        f"session:{context.session_id}"
    )

    tool_call_count = 0
    input_tokens = 0
    output_tokens = 0

    try:
        async for chunk, metadata in graph.astream(
            initial,
            config={
                "configurable": {"thread_id": thread_id},
                "recursion_limit": get_settings().graph_recursion_limit,
            },
            stream_mode="messages",
        ):
            msg = cast(Any, chunk)
            meta = cast(dict[str, Any], metadata)
            node = str(meta.get("langgraph_node", ""))
            usage = getattr(msg, "usage_metadata", None) or {}
            if isinstance(usage, dict):
                input_tokens += int(usage.get("input_tokens", 0) or 0)
                output_tokens += int(usage.get("output_tokens", 0) or 0)

            for tool_call in getattr(msg, "tool_calls", None) or []:
                sse = track.emit_tool_start(tool_call)
                if sse:
                    yield sse
                    tool_call_count += 1

            name = getattr(msg, "name", None)
            content = getattr(msg, "content", None)
            if node in {"read_tool", "write_tool"} and name and content:
                call_id = str(getattr(msg, "tool_call_id", ""))
                yield track.emit_tool_result(call_id, name, content)
            elif content and node == "model":
                yield track.emit_model_text(content)

    except asyncio.CancelledError:
        store_usage(
            db,
            context,
            run_id,
            model_config.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status="cancelled",
        )
        audit.record_run_end(run_id, status="cancelled", message="客户端取消运行")
        raise
    except GeneratorExit:
        audit.record_run_end(run_id, status="cancelled", message="客户端关闭连接")
        raise
    except Exception as e:  # noqa: BLE001  # 运行异常统一落库统计并向客户端发出错误事件
        error_message = redact_text(str(e))
        store_usage(
            db,
            context,
            run_id,
            model_config.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status="failed",
            error_message=error_message[:500],
        )
        audit.record_run_end(run_id, status="failed", message=str(e))
        is_agent_error = isinstance(e, AgentError)
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-error",
                run_id=run_id,
                code=e.code if is_agent_error else "AGENT_INTERNAL_ERROR",
                message=redact_text(str(e))
                if is_agent_error
                else "Agent 运行失败，请稍后重试",
                retryable=e.retryable if is_agent_error else False,
            )
        )
        return

    snapshot = await graph.aget_state(
        config={
            "configurable": {"thread_id": thread_id},
            "recursion_limit": get_settings().graph_recursion_limit,
        }
    )

    pending = snapshot.values.get("pending_approval")
    if snapshot.next and "approval_interrupt" in snapshot.next and pending:
        store_usage(
            db,
            context,
            run_id,
            model_config.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status="pending_confirmation",
        )
        audit.record_run_end(
            run_id, status="pending_confirmation", message="等待用户确认"
        )
        audit.record_approval_required(
            run_id=run_id,
            approval_id=pending["approval_id"],
            tool=pending["tool"],
            risk_level=pending["risk_level"],
            reasons=pending["reasons"],
        )
        yield encode_sse_event(
            ApprovalRequired(
                event_id=f"{run_id}-approval",
                run_id=run_id,
                session_id=context.session_id,
                approval_id=pending["approval_id"],
                operator=pending["tool"],
                call_id=pending.get("call_id", ""),
                risk_level=pending["risk_level"],
                reasons=pending["reasons"],
                preview=pending["preview"],
            )
        )
        yield encode_sse_event(
            RunCompleted(
                event_id=f"{run_id}-pending",
                run_id=run_id,
                session_id=context.session_id,
                status="pending_confirmation",
            )
        )
        return

    collected = track.collected
    if collected.strip():
        db.add(
            ChatMessage(
                session_id=context.session_id,
                role="assistant",
                content=collected.strip(),
            )
        )
        db.commit()

    store_usage(
        db,
        context,
        run_id,
        model_config.name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        tool_call_count=tool_call_count,
        status="completed",
    )
    audit.record_run_end(run_id, status="completed")
    yield encode_sse_event(
        RunCompleted(
            event_id=f"{run_id}-done", run_id=run_id, session_id=context.session_id
        )
    )
