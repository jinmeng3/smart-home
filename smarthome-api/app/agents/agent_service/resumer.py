import asyncio
from collections.abc import AsyncGenerator
from typing import Any, cast
from uuid import uuid4

from app.agents.agent_service.lease import acquire_run_lease, release_run_lease
from app.agents.agent_service.pending import is_pending_expired
from app.agents.agent_service.runner import (
    _create_graph_runner,
    _maybe_compact_tree,
    _sync_session_tree,
)
from app.agents.context import AgentContext
from app.agents.errors import AgentApprovalExpiredError, AgentError
from app.agents.events.sse import encode_sse_event
from app.agents.events.stream_tracker import StreamTracker
from app.agents.redaction import redact_text
from app.agents.usage import store_usage, update_run_phase
from app.core.config import get_settings
from app.models.ai import AIModel
from app.models.chat import ChatMessage
from app.schemas.sse import (
    Error,
    RunCompleted,
)
from app.services.session_tree import mirror_assistant_message
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
    """提交审批决定并以原模型恢复执行（带会话租约，§4.4）。"""
    thread_id = agent_thread_id(context)
    acquired = acquire_run_lease(
        db,
        user_id=context.user_id,
        household_id=context.household_id,
        session_id=context.session_id,
        run_id=f"run-{uuid4().hex}",
        thread_id=thread_id,
    )
    if not acquired:
        yield encode_sse_event(
            Error(
                event_id=f"decision-{context.session_id}-lease-error",
                run_id="",
                code="AGENT_CONCURRENT_RUN",
                message="该会话正在运行中，请等待当前操作完成后再试",
                retryable=False,
            )
        )
        return
    try:
        async for event in _resume_agent_body(
            context, decision, model_config, db
        ):
            yield event
    finally:
        release_run_lease(
            db,
            user_id=context.user_id,
            household_id=context.household_id,
            session_id=context.session_id,
        )


async def _resume_agent_body(
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
    except Exception:  # noqa: BLE001  # 初始化解析失败归为一类错误事件返回
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

    if is_pending_expired(pending):
        yield encode_sse_event(
            Error(
                event_id=f"{pending.get('run_id', '')}-approval-expired",
                run_id=pending.get("run_id", ""),
                code=AgentApprovalExpiredError.code,
                message="待审批操作已过期，请重新发起操作并确认",
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
    tracker = StreamTracker(run_id, context.session_id)
    input_tokens = 0
    output_tokens = 0
    last_input_tokens = 0
    last_output_tokens = 0
    tool_call_count = 0
    run_errored = False

    audit.record_approval_decision(
        run_id=run_id,
        approval_id=decision["approval_id"],
        decision=decision["decision"],
    )

    if decision.get("decision") == "approve":
        update_run_phase(db, run_id, "submitted")
        yield tracker.emit_execution_status(
            call_id=str(pending.get("call_id", "")),
            operator=str(pending.get("tool", "")),
            status="running",
            message="操作已确认，开始执行",
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
            usage = getattr(message, "usage_metadata", None) or {}
            if isinstance(usage, dict):
                input_tokens += int(usage.get("input_tokens", 0) or 0)
                output_tokens += int(usage.get("output_tokens", 0) or 0)
                last_input_tokens = int(usage.get("input_tokens", 0) or 0)
                last_output_tokens = int(usage.get("output_tokens", 0) or 0)

            chunk_result = tracker.emit_stream_chunk(message, node)
            for ev in chunk_result.events:
                yield ev
            tool_call_count += chunk_result.tool_call_delta
            if chunk_result.write_result_failed:
                run_errored = True
            # 流式消息的 content 已通过 emit_stream_chunk 处理完毕，
            # 不再需要单独处理 model content（collected 已由 emit_model_text 累加）

    except asyncio.CancelledError:
        audit.record_run_end(
            run_id,
            status="disconnected",
            message="客户端在确认恢复后断开连接",
        )
        raise
    except Exception as exc:  # noqa: BLE001  # 执行异常统一落库统计并向客户端发出错误事件
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

    try:
        assistant_message_id: int | None = None
        if tracker.collected.strip():
            assistant_message = ChatMessage(
                session_id=context.session_id,
                role="assistant",
                content=tracker.collected.strip(),
            )
            db.add(assistant_message)
            db.commit()
            assistant_message_id = assistant_message.id
            _sync_session_tree(
                context.session_id,
                lambda: mirror_assistant_message(
                    context.session_id,
                    tracker.collected.strip(),
                    usage={
                        "input": last_input_tokens,
                        "output": last_output_tokens,
                        "totalTokens": last_input_tokens + last_output_tokens,
                    },
                ),
            )
            await asyncio.to_thread(_maybe_compact_tree, context, model_config)

        store_usage(
            db,
            context,
            run_id,
            model_config.name,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status=("failed" if run_errored else "completed"),
        )
        audit.record_run_end(run_id, status=("failed" if run_errored else "completed"))

        yield encode_sse_event(
            RunCompleted(
                event_id=f"{run_id}-done",
                run_id=run_id,
                session_id=context.session_id,
                status=("failed" if run_errored else "completed"),
                message_id=assistant_message_id,
            )
        )
    except Exception as exc:  # noqa: BLE001  # 收尾异常同样以 SSE 错误事件返回，避免响应已开始后抛错
        error_message = redact_text(str(exc))
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
        audit.record_run_end(run_id, status="failed", message=str(exc))
        is_agent_error = isinstance(exc, AgentError)
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-finalize-error",
                run_id=run_id,
                code=exc.code if is_agent_error else "AGENT_FINALIZE_ERROR",
                message=redact_text(str(exc))
                if is_agent_error
                else "Agent 结果处理失败，请稍后重试",
                retryable=exc.retryable if is_agent_error else False,
            )
        )
        return
