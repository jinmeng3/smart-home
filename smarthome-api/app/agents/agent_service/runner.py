import asyncio
import logging
import time
from collections.abc import AsyncGenerator
from typing import Any, cast
from uuid import uuid4

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph.state import CompiledStateGraph
from sqlalchemy.orm import Session

from app.agents.agent_service.lease import get_run_lease, release_run_lease
from app.agents.audit.recorder import AuditRecorder, get_audit_recorder
from app.agents.checkpointer import get_checkpointer
from app.agents.context import AgentContext
from app.agents.errors import AgentError
from app.agents.events.sse import encode_sse_event
from app.agents.events.stream_tracker import StreamTracker
from app.agents.graph import build_graph
from app.agents.prompts import PROMPT_VERSION, system_prompt
from app.agents.rate_limiter import check_daily_budget, check_rate_limit
from app.agents.redaction import redact_text
from app.agents.subagents.context_engine import (
    ContextResolution,
    get_context_engine,
)
from app.agents.subagents.domain_router import is_write_domain, resolve_delegated_domain
from app.agents.subagents.domains import (
    AUTOMATION_SYSTEM_PROMPT,
    DEVICE_SYSTEM_PROMPT,
    SCENE_SYSTEM_PROMPT,
    SECURITY_SYSTEM_PROMPT,
)
from app.agents.subagents.funnel_router import (
    LAYER_CONTEXT,
    LAYER_RULE,
    RouteResult,
    SessionState,
    get_funnel_router,
)
from app.agents.subagents.rule_layer import execute_rule_layer
from app.agents.tools import get_domain_tools, get_household_tools
from app.agents.usage import start_run, store_usage, update_run_phase
from app.api.deps import get_model_cache
from app.compaction.summarize import create_langchain_summarizer
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
    mirror_subagent,
    mirror_user_message,
)

logger = logging.getLogger(__name__)

_DOMAIN_SYSTEM_PROMPTS: dict[str, str] = {
    "device": DEVICE_SYSTEM_PROMPT,
    "automation": AUTOMATION_SYSTEM_PROMPT,
    "scene": SCENE_SYSTEM_PROMPT,
    "security": SECURITY_SYSTEM_PROMPT,
}


def _route_funnel(context: AgentContext, message: str) -> RouteResult:
    """调用漏斗路由器以决定进入哪一层（规则层 / 上下文层 / 兜底层）。"""
    router = get_funnel_router()
    state = SessionState(
        session_id=context.session_id,
        household_id=context.household_id,
    )
    return router.route(message, state)


def _load_previous_user_message(session_id: int, current_message: str) -> str:
    """从会话树历史中提取「当前消息之前」的最后一条用户消息。

    上下文层（P1）指代消解的输入。任何失败（树未建 / 无历史 / 取不到）都返回
    空串，让 ``ContextEngine`` 转入兜底层，不中断主流程。
    """
    try:
        messages = build_context_messages(session_id)
    except Exception:  # noqa: BLE001  # 树读取失败 → 无上一轮可继承，安全回退
        return ""
    current = (current_message or "").strip()
    for msg in reversed(messages):
        if getattr(msg, "type", "") != "human":
            continue
        content = str(getattr(msg, "content", "")).strip()
        if content == current:
            # 重试 / 已落库场景下当前消息可能已在树中，跳过它取再上一轮
            continue
        return content
    return ""


def _resolve_context_turn(context: AgentContext, message: str) -> ContextResolution:
    """执行上下文层消解；未命中（绝大多数异常）一律返回 ``matched=False``。"""
    previous = _load_previous_user_message(context.session_id, message)
    if not previous:
        return ContextResolution(
            matched=False, needs_fallback=True, explanation="无上一轮可继承 → 兜底层"
        )
    return get_context_engine().resolve(message, previous_user_message=previous)


def _build_thread_id(context: AgentContext, domain: str | None) -> str:
    """构造 run 使用的 checkpoint thread_id。"""
    base = (
        f"user:{context.user_id}:household:{context.household_id}:"
        f"session:{context.session_id}"
    )
    if domain is not None and not is_write_domain(domain):
        return f"{base}:subagent:{domain}"
    return base


async def _create_graph_runner(
    context: AgentContext,
    db: Session,
    model_config: AIModel,
    *,
    domain: str | None = None,
    include_write: bool = False,
) -> tuple[CompiledStateGraph, AuditRecorder]:
    model = get_model_cache().get(model_config)
    tools = (
        get_domain_tools(domain, context, db, include_write=include_write)
        if domain is not None
        else get_household_tools(context, db)
    )
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
    model_id: int | None = None,
    domain: str | None = None,
) -> dict[str, Any]:
    domain_prompt = _DOMAIN_SYSTEM_PROMPTS.get(domain) if domain else None
    if domain_prompt is not None:
        sys_prompt = f"{domain_prompt}\n\n当前家庭：{household_name or '当前家庭'}"
    else:
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
        "model_id": model_id,
        "prompt_version": PROMPT_VERSION,
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
        context_window = (
            model_config.context_window or settings.session_tree_context_window
        )
        model = get_model_cache().get(model_config)
        summarizer = create_langchain_summarizer(model)
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
    domain = resolve_delegated_domain(message)
    thread_id = _build_thread_id(context, domain)
    acquired = get_run_lease(
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
                event_id=f"run-{uuid4().hex}-lease-error",
                run_id="",
                code="AGENT_CONCURRENT_RUN",
                message="该会话正在运行中，请等待当前操作完成后再试",
                retryable=False,
            )
        )
        return
    try:
        async for event in _run_agent_body(
            context,
            household_name,
            message,
            model_config,
            db,
            history_messages=history_messages,
            persist_user_message=persist_user_message,
        ):
            yield event
    finally:
        release_run_lease(
            db,
            user_id=context.user_id,
            household_id=context.household_id,
            session_id=context.session_id,
        )


async def _run_agent_body(
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
    funnel_decision = _route_funnel(context, message)
    if funnel_decision.layer == LAYER_RULE and funnel_decision.rule_result is not None:
        async for event in execute_rule_layer(
            context=context,
            household_name=household_name,
            message=message,
            model_name=model_config.name,
            model_id=model_config.id,
            db=db,
            rule_result=funnel_decision.rule_result,
        ):
            yield event
        return

    # LAYER_CONTEXT（P1 上下文层）：多轮 / 指代消解先于 LLM（§6）；
    # 未命中或功能关闭时再归还兜底层（LLM 主图）。
    if funnel_decision.layer == LAYER_CONTEXT and get_settings().funnel_context_enabled:
        context_resolution = _resolve_context_turn(context, message)
        if context_resolution.matched and context_resolution.rule_result is not None:
            async for event in execute_rule_layer(
                context=context,
                household_name=household_name,
                message=message,
                model_name=model_config.name,
                model_id=model_config.id,
                db=db,
                rule_result=context_resolution.rule_result,
            ):
                yield event
            return

    # LAYER_FALLBACK / 未消解的 LAYER_CONTEXT 都走原图（兜底层）。
    domain = resolve_delegated_domain(message)
    include_write = is_write_domain(domain)

    try:
        check_rate_limit(context.user_id)
        check_daily_budget(db, context.user_id)
        graph, audit = await _create_graph_runner(
            context, db, model_config, domain=domain, include_write=include_write
        )
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

    base_thread_id = (
        f"user:{context.user_id}:household:{context.household_id}:"
        f"session:{context.session_id}"
    )

    if domain is not None and not include_write:
        # 只读子 Agent：单轮查询，不加载会话树历史，并使用独立 thread 隔离 checkpoint
        thread_id = f"{base_thread_id}:subagent:{domain}"
    else:
        # 主图 或 写能力域子 Agent：共用 thread_id，保证审批状态可被 resume_agent 找到
        thread_id = base_thread_id
        if history_messages is None:
            history_messages = await _load_tree_history(context.session_id, thread_id)

    if persist_user_message:
        db.add(ChatMessage(session_id=context.session_id, role="user", content=message))
        db.commit()
        _sync_session_tree(
            context.session_id, lambda: mirror_user_message(context.session_id, message)
        )

    audit.record_run_start(context, run_id)
    subagent_started_at: float | None = None
    if domain is not None:
        subagent_started_at = time.perf_counter()
        audit.record_subagent_start(run_id=run_id, domain=domain, task=message)
    start_run(db, context, run_id, model_config.name, domain=domain)

    initial = _init_state(
        context,
        household_name,
        message,
        run_id,
        db,
        history_messages,
        model_config.name,
        model_id=model_config.id,
        domain=domain,
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

            chunk_result = track.emit_stream_chunk(msg, node)
            for ev in chunk_result.events:
                yield ev
            tool_call_count += chunk_result.tool_call_delta
            # 写工具提交时更新阶段状态并发送 "submitted" 状态事件（runner 特有，§5.3）
            if chunk_result.write_submit_names:
                update_run_phase(db, run_id, "submitted")
                for tc_name in chunk_result.write_submit_names:
                    yield track.emit_execution_status(
                        call_id="",
                        operator=tc_name,
                        status="submitted",
                        message="写操作已提交，等待风险评估",
                    )
            elif chunk_result.tool_call_delta:
                update_run_phase(db, run_id, "executing")

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

    try:
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
            if domain is not None:
                audit.record_subagent_end(
                    run_id=run_id, domain=domain, status="pending_confirmation"
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
            if domain is not None:
                _sync_session_tree(
                    context.session_id,
                    lambda: mirror_subagent(
                        context.session_id,
                        domain,
                        message,
                        collected.strip(),
                        usage={
                            "input": last_input_tokens,
                            "output": last_output_tokens,
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
        if domain is not None:
            duration_ms = (
                int((time.perf_counter() - subagent_started_at) * 1000)
                if subagent_started_at is not None
                else None
            )
            audit.record_subagent_end(
                run_id=run_id,
                domain=domain,
                status="completed",
                summary=collected.strip(),
                duration_ms=duration_ms,
                usage={"input": input_tokens, "output": output_tokens},
            )
            logger.info(
                "subagent_run_completed run_id=%s domain=%s duration_ms=%s",
                run_id,
                domain,
                duration_ms,
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
    except Exception as e:  # noqa: BLE001  # 收尾异常同样以 SSE 错误事件返回，避免响应已开始后抛错
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
                event_id=f"{run_id}-finalize-error",
                run_id=run_id,
                code=e.code if is_agent_error else "AGENT_FINALIZE_ERROR",
                message=redact_text(str(e))
                if is_agent_error
                else "Agent 结果处理失败，请稍后重试",
                retryable=e.retryable if is_agent_error else False,
            )
        )
        return
