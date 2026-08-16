import asyncio
import json
from collections.abc import AsyncGenerator
from typing import Any, cast

from app.agents.agent_service.runner import _create_graph_runner
from app.agents.context import AgentContext
from app.agents.events.models import (
    Error,
    ExecutionStatus,
    RunCompleted,
)
from app.agents.events.sse import encode_sse_event
from app.agents.events.stream_tracker import StreamTracker
from app.agents.redaction import redact_text
from app.core.config import get_settings
from app.models.ai import AIModel
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
    graph, audit = await _create_graph_runner(context, db, model_config)

    config: RunnableConfig = {
        "configurable": {"thread_id": agent_thread_id(context)},
        "recursion_limit": get_settings().graph_recursion_limit,
    }

    snapshot = await graph.aget_state(config)
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
        audit.record_run_end(run_id, status="failed", message=str(exc))
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-resume-error",
                run_id=run_id,
                message=redact_text(str(exc)),
                retryable=False,
            )
        )
        return

    audit.record_run_end(run_id, status="completed")

    yield encode_sse_event(
        RunCompleted(
            event_id=f"{run_id}-done",
            run_id=run_id,
            session_id=context.session_id,
        )
    )
