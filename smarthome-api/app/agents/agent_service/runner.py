import asyncio
import logging
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
from app.agents.rate_limiter import check_daily_budget, check_rate_limit
from app.agents.redaction import redact_text
from app.agents.tools import WRITE_TOOL_NAMES, get_household_tools
from app.agents.usage import start_run, store_usage, update_run_phase
from app.api.deps import get_model_cache
from app.compaction.summarize import langchain_summarizer
from app.core.config import get_settings
from app.models.ai import AIModel
from app.models.chat import ChatMessage
from app.schemas.sse import (
    ApprovalRequired,
    Error,
    RunCompleted,
    RunStarted,
)
from app.services.session_tree import (
    build_context_messages,
    compact_if_needed,
    mirror_assistant_message,
    mirror_user_message,
)
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


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
    history_messages: list | None = None,
    model_name: str = "",
) -> dict[str, Any]:
    sys_prompt = system_prompt(context, household_name, db, message)
    messages: list = [SystemMessage(content=sys_prompt)]
    if history_messages:
        messages.extend(history_messages)
    messages.append(HumanMessage(content=message))
    return {
        "messages": messages,
        "context": context,
        "run_id": run_id,
        "rounds": 0,
        "model_name": model_name,
    }


def _sync_session_tree(session_id: int, action) -> None:
    """会话树镜像接入；任何失败仅记录日志，不影响 Agent 主流程。"""
    try:
        action()
    except Exception:  # 接入层失败不应中断主流程
        logger.warning("会话树接入失败，已忽略", exc_info=True)


def _maybe_compact_tree(context: AgentContext, model_config: AIModel) -> None:
    """上下文超限时压缩会话树（需 ``COMPACTION_ENABLED=true``）。

    在独立线程执行，避免同步 LLM 调用阻塞事件循环；任何失败仅记录日志。
    """
    try:
        settings = get_settings()
        if not settings.compaction_enabled:
            return
        context_window = model_config.context_window or settings.session_tree_context_window
        model = get_model_cache().get(model_config)
        summarizer = langchain_summarizer(model)
        compact_if_needed(
            context.session_id,
            summarizer=summarizer,
            context_window=context_window,
        )
    except Exception:  # 压缩失败不应中断主流程
        logger.warning("上下文压缩失败，已忽略", exc_info=True)


async def _load_tree_history(session_id: int, thread_id: str) -> list | None:
    """从会话树加载（压缩后）历史，并清除 checkpointer 旧历史。

    任何失败（树读取或 checkpointer 清除）都回退为 None，沿用 checkpointer 历史，
    不中断主流程。
    """
    try:
        history = build_context_messages(session_id)
        saver = await get_checkpointer()
        await saver.adelete_thread(thread_id)
    except Exception:  # 树历史加载失败回退到 checkpointer 历史
        logger.warning("会话树历史加载失败，回退到 checkpointer 历史", exc_info=True)
        return None
    return history


async def run_agent(
    context: AgentContext,
    household_name: str,
    message: str,
    model_config: AIModel,
    db: Session,
    *,
    history_messages: list | None = None,
    persist_user_message: bool = True,
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

    track = StreamTracker(run_id, context.session_id)
    yield encode_sse_event(
        RunStarted(
            event_id=f"{run_id}-start",
            run_id=run_id,
            session_id=context.session_id,
            household_id=context.household_id,
        )
    )

    thread_id = (
        f"user:{context.user_id}:household:{context.household_id}:"
        f"session:{context.session_id}"
    )

    # 正常 run（非 regenerate）：从会话树加载（压缩后）历史作为 Agent 上下文，
    # 并清除 checkpointer 旧历史，避免与树历史重复累积。
    if history_messages is None:
        history_messages = await _load_tree_history(context.session_id, thread_id)

    if persist_user_message:
        db.add(ChatMessage(session_id=context.session_id, role="user", content=message))
        db.commit()
        _sync_session_tree(
            context.session_id, lambda: mirror_user_message(context.session_id, message)
        )

    audit.record_run_start(context, run_id)
    start_run(db, context, run_id, model_config.name)

    initial = _init_state(
        context,
        household_name,
        message,
        run_id,
        db,
        history_messages,
        model_config.name,
    )

    tool_call_count = 0
    input_tokens = 0
    output_tokens = 0
    last_input_tokens = 0
    last_output_tokens = 0

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
                # 记录最后一次调用的上下文规模，用于会话树 token 估算
                last_input_tokens = int(usage.get("input_tokens", 0) or 0)
                last_output_tokens = int(usage.get("output_tokens", 0) or 0)

            for tool_call in getattr(msg, "tool_calls", None) or []:
                sse = track.emit_tool_start(tool_call)
                if sse:
                    yield sse
                    tool_call_count += 1
                tc = (
                    tool_call if isinstance(tool_call, dict) else tool_call.model_dump()
                )
                tc_name = str(tc.get("name", ""))
                if tc_name in WRITE_TOOL_NAMES:
                    update_run_phase(db, run_id, "submitted")
                    yield track.emit_execution_status(
                        call_id=str(tc.get("id", "")),
                        operator=tc_name,
                        status="submitted",
                        message="写操作已提交，等待风险评估",
                    )
                else:
                    update_run_phase(db, run_id, "executing")

            name = getattr(msg, "name", None)
            content = getattr(msg, "content", None)
            if node in {"read_tool", "write_tool"} and name and content:
                call_id = str(getattr(msg, "tool_call_id", ""))
                yield track.emit_tool_result(call_id, name, content)
                if node == "write_tool":
                    yield track.emit_execution_result(call_id, name, content)
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
    assistant_message_id: int | None = None
    if collected.strip():
        assistant_message = ChatMessage(
            session_id=context.session_id,
            role="assistant",
            content=collected.strip(),
        )
        db.add(assistant_message)
        db.commit()
        assistant_message_id = assistant_message.id
        _sync_session_tree(
            context.session_id,
            lambda: mirror_assistant_message(
                context.session_id,
                collected.strip(),
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
        status="completed",
    )
    audit.record_run_end(run_id, status="completed")
    yield encode_sse_event(
        RunCompleted(
            event_id=f"{run_id}-done",
            run_id=run_id,
            session_id=context.session_id,
            message_id=assistant_message_id,
        )
    )
