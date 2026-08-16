import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any, cast

from app.agents.agent_service.runner import _create_graph_runner
from app.agents.context import AgentContext
from app.agents.errors import AgentError
from app.agents.events.models import (
    Error,
    ExecutionStatus,
    RunCompleted,
)
from app.agents.events.sse import encode_sse_event
from app.agents.events.stream_tracker import StreamTracker
from app.agents.rate_limiter import store_usage
from app.agents.redaction import redact_text
from app.core.config import get_settings
from app.models.ai import AIModel
from app.models.chat import ChatMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import Command
from sqlalchemy.orm import Session


def agent_thread_id(context: AgentContext) -> str:
    return (
        f"user:{context.user_id}:household:{context.household_id}:"
        f"session:{context.session_id}"
    )


async def resume_agent(
    context: AgentContext,
    decision: dict[str, Any],
    model_config: AIModel,
    db: Session,
) -> AsyncGenerator[str, None]:
    config: RunnableConfig = {
        "configurable": {"thread_id": agent_thread_id(context)},
        "recursion_limit": get_settings().graph_recursion_limit,
    }
    try:
        graph, audit = await _create_graph_runner(context, db, model_config)
        snapshot = await graph.aget_state(config)
    except AgentError as exc:
        yield encode_sse_event(
            Error(
                event_id=f"decision-{context.session_id}-setup-error",
                run_id="",
                code=exc.code,
                message=redact_text(str(exc)),
                retryable=exc.retryable,
            )
        )
        return
    except Exception:  # noqa: BLE001
        # 兜底保护：捕获 _create_graph_runner 或 aget_state 中
        # 出现的非 AgentError 意外异常（如数据库连接失败、超时等）
        yield encode_sse_event(
            Error(
                event_id=f"decision-{context.session_id}-setup-error",
                run_id="",
                message="Agent 恢复失败，请检查服务配置",
                retryable=False,
            )
        )
        return
    pending = snapshot.values.get("pending_approval")

    if not pending:
        yield encode_sse_event(
            Error(
                event_id=f"decision-{context.session_id}-missing",
                run_id="",
                code="AGENT_APPROVAL_NOT_FOUND",
                message="当前会话没有待确认操作",
                retryable=False,
            )
        )
        return

    if pending["approval_id"] != decision["approval_id"]:
        yield encode_sse_event(
            Error(
                event_id=f"{pending['run_id']}-approval-mismatch",
                run_id=pending["run_id"],
                code="AGENT_APPROVAL_MISMATCH",
                message="确认请求已失效或不属于当前操作",
                retryable=False,
            )
        )
        return

    run_id = pending["run_id"]
    tracker = StreamTracker(run_id)
    input_tokens = 0
    output_tokens = 0
    tool_call_count = 0

    # 记录用户的确认决策
    audit.record_approval_decision(
        run_id=run_id,
        approval_id=decision["approval_id"],
        decision=decision["decision"],
    )

    try:
        async for chunk, metadata in graph.astream(
            Command(resume=decision),
            config=config,
            stream_mode="messages",
        ):
            message = cast(Any, chunk)
            meta = cast(dict[str, Any], metadata)
            node = str(meta.get("langgraph_node", ""))
            content = getattr(message, "content", None)
            usage = getattr(message, "usage_metadata", None) or {}
            if isinstance(usage, dict):
                input_tokens += int(usage.get("input_tokens", 0) or 0)
                output_tokens += int(usage.get("output_tokens", 0) or 0)

            for tool_call in getattr(message, "tool_calls", None) or []:
                event = tracker.emit_tool_start(tool_call)
                if event:
                    yield event
                    tool_call_count += 1

            if node == "write_tool" and content:
                payload = json.loads(content)

                yield encode_sse_event(
                    ExecutionStatus(
                        event_id=f"{run_id}-execution",
                        run_id=run_id,
                        session_id=context.session_id,
                        operator=pending["tool"],
                        status=payload.get("status", "unknown"),
                        execution_id=payload.get("execution_id"),
                        message=payload.get("message", payload.get("error", "")),
                    )
                )

            elif node == "read_tool" and content:
                call_id = str(getattr(message, "tool_call_id", ""))
                name = str(getattr(message, "name", ""))
                yield tracker.emit_tool_result(call_id, name, content)
            elif node == "model" and content:
                yield tracker.emit_model_text(content)

    except asyncio.CancelledError:
        audit.record_run_end(
            run_id,
            status="disconnected",
            message="客户端在确认恢复后断开连接",
        )
        raise
    except Exception as exc:  # noqa: BLE001
        store_usage(
            db,
            context,
            run_id,
            model_config.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status="failed",
            error_message=redact_text(str(exc))[:500],
        )
        audit.record_run_end(run_id, status="failed", message=str(exc))
        is_agent_error = isinstance(exc, AgentError)
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-resume-error",
                run_id=run_id,
                code=exc.code if is_agent_error else "AGENT_INTERNAL_ERROR",
                message=(
                    redact_text(str(exc))
                    if is_agent_error
                    else "Agent 恢复执行失败，请稍后重试"
                ),
                retryable=exc.retryable if is_agent_error else False,
            )
        )
        return

    if tracker.collected.strip():
        db.add(
            ChatMessage(
                session_id=context.session_id,
                role="assistant",
                content=tracker.collected.strip(),
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
            event_id=f"{run_id}-done",
            run_id=run_id,
            session_id=context.session_id,
        )
    )
