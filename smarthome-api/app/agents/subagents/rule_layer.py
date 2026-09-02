from __future__ import annotations

import logging
import time
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agents.audit.recorder import get_audit_recorder
from app.agents.context import AgentContext
from app.agents.errors import AgentError
from app.agents.events.sse import encode_sse_event
from app.agents.rate_limiter import check_daily_budget, check_rate_limit
from app.agents.redaction import redact_text
from app.agents.risk import (
    classify_device_operation,
    classify_scene_execution,
)
from app.agents.risk.policy import RiskLevel
from app.agents.subagents.lexicon import get_lexicon
from app.agents.subagents.rule_engine import (
    RuleParseResult,
    WriteProposal,
)
from app.agents.tools import WRITE_TOOL_SCHEMAS
from app.agents.tools.execute.devices import (
    set_curtain_position,
    set_device_power,
    set_device_temperature,
)
from app.agents.tools.execute.scenes import execute_scene_operation
from app.agents.usage import store_usage
from app.core.config import get_settings
from app.models.device import Device, DeviceStatus
from app.models.scene import Scene
from app.schemas.sse import (
    ApprovalRequired,
    Error,
    ExecutionStatus,
    MessageDelta,
    RunCompleted,
    RunStarted,
    ToolCompleted,
    ToolStarted,
)
from app.utils.json import dump_json
from app.utils.time import now_utc

logger = logging.getLogger(__name__)


@dataclass
class ProposalOutcome:
    """单个写提案的执行结果（用于跨事件循环传递状态）。"""

    tool: str
    status: str  # completed / pending_confirmation / failed
    message: str
    pending: dict | None = None
    result_payload: dict | None = None
    resolved_args: dict | None = None


# === 设备反查与参数校验 ===


def _split_room_from_entity_ref(entity_ref: str, room_hint: str) -> str:
    """从 ``entity_ref`` 中提取房间名（如「客厅灯」 → 「客厅」）。"""
    if room_hint:
        return room_hint
    if not entity_ref:
        return ""
    for keyword in sorted(get_lexicon().device_hints, key=len, reverse=True):
        if entity_ref.endswith(keyword):
            return entity_ref[: -len(keyword)]
    return ""


def _resolve_device(
    db: Session,
    context: AgentContext,
    *,
    entity_type: str,
    entity_ref: str,
    room: str,
) -> Device | None:
    """按 ``entity_ref`` + ``room`` + ``entity_type`` 反查家庭设备。

    严格匹配规则（按优先级）：

    1. ``entity_ref`` 精确匹配 ``Device.name``；
    2. 否则按 ``room + entity_type`` 组合筛选；
    3. 命中数量 != 1 时尝试名称包含匹配，仍不唯一则返回 None。
    """
    target_name = entity_ref.strip()
    if target_name:
        device = db.scalar(
            select(Device).where(
                Device.household_id == context.household_id,
                Device.name == target_name,
            )
        )
        if device is not None:
            return device

    query = select(Device).where(Device.household_id == context.household_id)
    if room:
        query = query.where(Device.room == room)
    if entity_type and entity_type != "device":
        query = query.where(Device.type == entity_type)
    candidates = list(db.scalars(query).all())
    if len(candidates) == 1:
        return candidates[0]
    for cand in candidates:
        if target_name and (target_name in cand.name or cand.name in target_name):
            return cand
    return None


def _make_args(tool: str, base_args: dict, *, device_id: int) -> dict:
    """把规则层产出的「待解析」args 与反查到的 device_id 合并，并经 Pydantic 校验。"""
    merged = dict(base_args)
    merged["device_id"] = device_id
    schema = WRITE_TOOL_SCHEMAS.get(tool)
    if schema is not None:
        return schema.model_validate(merged).model_dump(exclude_none=True)
    return merged


# === 场景反查 ===


def _resolve_scene(
    db: Session,
    context: AgentContext,
    scene_key: str,
) -> tuple[str, str]:
    """把场景意图标识（``home`` / ``leave`` ...）反查为本家庭的 ``Scene.id``。

    为什么需要这一步：``Scene.id`` 是全局唯一的 String(64) 主键，同一个
    「回家」场景在不同家庭里 id 各不相同，因此词表里只能存"意图标识"。

    匹配策略（按优先级，均限定当前家庭 + ``enabled=True``）：

    1. ``Scene.id == scene_key`` —— 兼容"场景被手动 seed 成该 id"的存量数据；
    2. ``Scene.name`` 精确等于某个候选名（``lexicon.scene_name_hints``）；
    3. ``Scene.name`` 包含某个候选名。

    Returns:
        ``(scene_id, error)``。成功时 ``error`` 为空串；失败 / 歧义时
        ``scene_id`` 为空串且 ``error`` 是面向用户的提示。**歧义时不猜**，
        交由上层追问，与 ``AliasIndex`` 冲突时返回空串是同一套约定。
    """
    key = (scene_key or "").strip()
    if not key:
        return "", "未识别出要执行的场景"

    base = select(Scene).where(
        Scene.household_id == context.household_id,
        Scene.enabled.is_(True),
    )

    # 1. 兼容：场景主键恰好就是意图标识
    exact_id = db.scalar(base.where(Scene.id == key))
    if exact_id is not None:
        return exact_id.id, ""

    hints = get_lexicon().scene_name_hints.get(key, ())
    if not hints:
        return "", f"本家庭没有配置「{key}」对应的场景，请先创建或改用完整场景名"

    candidates = list(db.scalars(base).all())
    if not candidates:
        return "", "本家庭还没有启用的场景，请先创建"

    # 2. 名称精确等于候选名
    exact_matches = [s for s in candidates if s.name.strip() in hints]
    if len(exact_matches) == 1:
        return exact_matches[0].id, ""
    if len(exact_matches) > 1:
        names = "、".join(s.name for s in exact_matches)
        return "", f"匹配到多个场景（{names}），请指明要执行哪一个"

    # 3. 名称包含候选名
    fuzzy = [s for s in candidates if any(hint in s.name for hint in hints)]
    if len(fuzzy) == 1:
        return fuzzy[0].id, ""
    if len(fuzzy) > 1:
        names = "、".join(s.name for s in fuzzy)
        return "", f"匹配到多个场景（{names}），请指明要执行哪一个"

    return "", f"未找到与「{key}」匹配的场景，请确认场景名称"


def _make_scene_args(base_args: dict, *, scene_id: str) -> dict:
    """把反查到的 ``scene_id`` 注入场景提案并经 Pydantic 校验。"""
    merged = dict(base_args)
    merged["scene_id"] = scene_id
    schema = WRITE_TOOL_SCHEMAS.get("execute_scene")
    if schema is not None:
        return schema.model_validate(merged).model_dump(exclude_none=True)
    return merged


# === 风险分类与 pending 构造 ===


def _classify_for_proposal(
    db: Session,
    context: AgentContext,
    proposal: WriteProposal,
) -> tuple[RiskLevel, list[str], dict, str]:
    """对规则层产出的写提案做风险分类（与主图 risk_check 完全一致）。"""
    tool = proposal.tool
    args = dict(proposal.args)

    if tool == "execute_scene":
        scene_id = str(args.get("scene_id", ""))
        decision = classify_scene_execution(db=db, context=context, scene_id=scene_id)
        return (
            decision.level,
            decision.reasons,
            decision.preview,
            decision.resource_version,
        )
    if tool in {"set_device_power", "set_device_temperature", "set_curtain_position"}:
        device_id = args.get("device_id")
        if device_id is None:
            return RiskLevel.UNKNOWN, ["缺少设备 ID"], {}, ""
        decision = classify_device_operation(
            db=db,
            context=context,
            operation=tool,
            device_id=int(device_id),
            args=args,
        )
        return (
            decision.level,
            decision.reasons,
            decision.preview,
            decision.resource_version,
        )
    return RiskLevel.UNKNOWN, [f"规则层不支持的写工具：{tool}"], {}, ""


def _build_pending(
    *,
    run_id: str,
    call_id: str,
    tool: str,
    args: dict,
    level: RiskLevel,
    reasons: list[str],
    preview: dict,
    resource_version: str,
    model_name: str,
    model_id: int | None,
    session_id: int,
) -> dict:
    """构造与主图 ``risk_check`` 同构的 pending_approval dict。"""
    now = now_utc()
    ttl = get_settings().approval_ttl_seconds
    return {
        "approval_id": f"{run_id}:{call_id}",
        "run_id": run_id,
        "session_id": session_id,
        "call_id": call_id,
        "tool": tool,
        "args": args,
        "risk_level": level.value,
        "reasons": reasons,
        "preview": preview,
        "resource_version": resource_version,
        "model_name": model_name,
        "model_id": model_id,
        "created_at": now.isoformat(),
        "expires_at": now.timestamp() + ttl,
    }


# === 真实写执行（复用 agents/tools/execute） ===


async def _execute_proposal(
    db: Session,
    context: AgentContext,
    proposal: WriteProposal,
) -> dict:
    """调用 ``agents/tools/execute`` 中的真实执行函数（与主图同源）。"""
    args = dict(proposal.args)
    if proposal.tool == "set_device_power":
        return set_device_power(
            db,
            context,
            device_id=int(args["device_id"]),
            power=str(args["power"]),
        )
    if proposal.tool == "set_device_temperature":
        return set_device_temperature(
            db,
            context,
            device_id=int(args["device_id"]),
            temperature=float(args["temperature"]),
            mode=args.get("mode"),
            fan_speed=args.get("fan_speed"),
        )
    if proposal.tool == "set_curtain_position":
        return set_curtain_position(
            db,
            context,
            device_id=int(args["device_id"]),
            position=int(args["position"]),
        )
    if proposal.tool == "execute_scene":
        return execute_scene_operation(db, context, args, {"resource_version": ""})
    return {
        "ok": False,
        "status": "failed",
        "code": "AGENT_UNKNOWN_TOOL",
        "error": f"规则层不支持的写工具：{proposal.tool}",
    }


async def _answer_simple_query(
    db: Session, context: AgentContext, rule_result: RuleParseResult
) -> str:
    """简单查询：直接读设备 State 缓存返回，避免 LLM 推理。"""
    entity = rule_result.entity
    room = rule_result.entity_ref
    if entity == "clock":
        return f"现在是 {time.strftime('%H:%M')}（本地时间）"

    device: Device | None = None
    if room:
        device = db.scalar(
            select(Device)
            .where(Device.household_id == context.household_id, Device.room == room)
            .limit(1)
        )
    if device is None:
        return f"未找到「{room or entity}」相关的设备，无法回答。"

    if entity == "temperature":
        # 当前没有真实温度字段（占位见 backend-agent-gap-analysis §3.2）。
        return f"「{device.name}」的温度字段尚未接入，敬请期待。"
    if entity == "humidity":
        return f"「{device.name}」的湿度字段尚未接入，敬请期待。"
    status_value = (
        device.status.value
        if isinstance(device.status, DeviceStatus)
        else device.status
    )
    return f"「{device.name}」当前状态：{status_value}。"


# === 公开入口：execute_rule_layer ===


async def execute_rule_layer(
    context: AgentContext,
    household_name: str,
    message: str,
    model_name: str,
    model_id: int | None,
    db: Session,
    rule_result: RuleParseResult,
) -> AsyncGenerator[str, None]:
    """执行规则层直接路径，作为 ``run_agent_body`` 的早退分支。

    返回的 SSE 事件序列与 LLM 主图同构，便于前端复用现有解析器：

    - ``run_started`` 永远先发
    - 写路径：``tool_started → tool_completed/execution_status → run_completed``
      或 ``approval_required → run_completed (pending_confirmation)``
    - 简单查询：``message_delta → run_completed``
    - 失败：``error → run_completed``

    任何异常（设备找不到 / 风险分类抛错 / DB 失败）一律不抛给上游，
    而是 yield ``Error`` 事件并以 ``failed`` 状态结束。
    """
    run_id = f"run-{uuid4().hex}"
    audit = get_audit_recorder()
    tool_call_count = 0
    input_tokens = 0
    output_tokens = 0
    final_status = "completed"
    final_message = ""
    error_message: str | None = None

    try:
        try:
            check_rate_limit(context.user_id)
            check_daily_budget(db, context.user_id)
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

        audit.record_run_start(context, run_id)
        yield encode_sse_event(
            RunStarted(
                event_id=f"{run_id}-start",
                run_id=run_id,
                session_id=context.session_id,
                household_id=context.household_id,
            )
        )

        # 1. 简单查询：直接走缓存 / 现查
        if rule_result.intent == "query":
            text = await _answer_simple_query(db, context, rule_result)
            yield encode_sse_event(
                MessageDelta(event_id=f"{run_id}-msg", run_id=run_id, content=text)
            )
            final_status = "completed"
            final_message = text
        elif not rule_result.write_proposals:
            yield encode_sse_event(
                Error(
                    event_id=f"{run_id}-no-proposal",
                    run_id=run_id,
                    code="AGENT_RULE_NO_PROPOSAL",
                    message="规则层未产出可执行提案",
                    retryable=False,
                )
            )
            final_status = "failed"
            error_message = "规则层未产出可执行提案"
        else:
            last_outcome: ProposalOutcome | None = None
            for index, proposal in enumerate(rule_result.write_proposals):
                outcome = await _execute_one_proposal(
                    context=context,
                    db=db,
                    run_id=run_id,
                    rule_result=rule_result,
                    proposal=proposal,
                    index=index,
                    model_name=model_name,
                    model_id=model_id,
                    audit=audit,
                )
                tool_call_count += 1
                last_outcome = outcome
                # 流式 yield 该提案的所有事件
                for event in outcome_events(run_id, context.session_id, outcome):
                    yield event
                if outcome.status in {"pending_confirmation", "failed"}:
                    break
            if last_outcome is not None:
                final_status = last_outcome.status
                final_message = last_outcome.message
                if final_status == "failed":
                    error_message = final_message

        # 2. 落库用量统计
        store_usage(
            db,
            context,
            run_id,
            model_name=model_name or "rule-layer",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            tool_call_count=tool_call_count,
            status=final_status,
            error_message=error_message,
            phase="thinking" if final_status == "completed" else "failed",
            domain=rule_result.domain or None,
        )
        audit.record_run_end(
            run_id,
            status=final_status,
            message=final_message or error_message or "",
        )
        yield encode_sse_event(
            RunCompleted(
                event_id=f"{run_id}-done",
                run_id=run_id,
                session_id=context.session_id,
                status=final_status,
            )
        )
    except AgentError as exc:
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-error",
                run_id=run_id,
                code=exc.code,
                message=redact_text(str(exc)),
                retryable=exc.retryable,
            )
        )
        audit.record_run_end(run_id, status="failed", message=str(exc))
    except Exception as exc:
        logger.exception("规则层直执失败 run_id=%s", run_id)
        yield encode_sse_event(
            Error(
                event_id=f"{run_id}-error",
                run_id=run_id,
                code="AGENT_INTERNAL_ERROR",
                message="规则层执行失败，请稍后重试",
                retryable=False,
            )
        )
        audit.record_run_end(run_id, status="failed", message=str(exc))


# === 内部：单提案执行 ===


async def _execute_one_proposal(
    *,
    context: AgentContext,
    db: Session,
    run_id: str,
    rule_result: RuleParseResult,
    proposal: WriteProposal,
    index: int,
    model_name: str,
    model_id: int | None,
    audit,
) -> ProposalOutcome:
    """处理单个写提案，返回 ``ProposalOutcome``（不直接 yield 事件）。"""
    call_id = f"{run_id}:{index}"
    started = time.perf_counter()

    # 1. 设备反查
    if proposal.tool in {
        "set_device_power",
        "set_device_temperature",
        "set_curtain_position",
    }:
        room = _split_room_from_entity_ref(rule_result.entity_ref, room_hint="")
        device = _resolve_device(
            db,
            context,
            entity_type=rule_result.entity,
            entity_ref=rule_result.entity_ref,
            room=room,
        )
        if device is None:
            error = f"未找到匹配「{rule_result.entity_ref}」的设备，请确认名称或房间"
            duration_ms = int((time.perf_counter() - started) * 1000)
            audit.record_tool_call(
                run_id=run_id,
                call_id=call_id,
                tool=proposal.tool,
                args=proposal.args,
                result={"ok": False, "error": error},
                ok=False,
                duration_ms=duration_ms,
            )
            return ProposalOutcome(
                tool=proposal.tool,
                status="failed",
                message=error,
                result_payload={"ok": False, "error": error},
            )
        try:
            resolved_args = _make_args(
                proposal.tool, proposal.args, device_id=device.id
            )
        except Exception as exc:  # noqa: BLE001
            error = f"规则层参数校验失败：{exc}"
            duration_ms = int((time.perf_counter() - started) * 1000)
            audit.record_tool_call(
                run_id=run_id,
                call_id=call_id,
                tool=proposal.tool,
                args=proposal.args,
                result={"ok": False, "error": error},
                ok=False,
                duration_ms=duration_ms,
            )
            return ProposalOutcome(
                tool=proposal.tool,
                status="failed",
                message=error,
                result_payload={"ok": False, "error": error},
            )
    else:
        resolved_args = dict(proposal.args)

    # 1b. 场景反查：规则层只给出意图标识，真实 Scene.id 必须按家庭查
    if proposal.tool == "execute_scene":
        scene_key = str(rule_result.params.get("scene_key") or rule_result.entity_ref)
        scene_id, scene_error = _resolve_scene(db, context, scene_key)
        if not scene_id:
            duration_ms = int((time.perf_counter() - started) * 1000)
            audit.record_tool_call(
                run_id=run_id,
                call_id=call_id,
                tool=proposal.tool,
                args=proposal.args,
                result={"ok": False, "error": scene_error},
                ok=False,
                duration_ms=duration_ms,
            )
            return ProposalOutcome(
                tool=proposal.tool,
                status="failed",
                message=scene_error,
                result_payload={"ok": False, "error": scene_error},
            )
        try:
            resolved_args = _make_scene_args(proposal.args, scene_id=scene_id)
        except Exception as exc:  # noqa: BLE001
            error = f"规则层场景参数校验失败：{exc}"
            duration_ms = int((time.perf_counter() - started) * 1000)
            audit.record_tool_call(
                run_id=run_id,
                call_id=call_id,
                tool=proposal.tool,
                args=proposal.args,
                result={"ok": False, "error": error},
                ok=False,
                duration_ms=duration_ms,
            )
            return ProposalOutcome(
                tool=proposal.tool,
                status="failed",
                message=error,
                result_payload={"ok": False, "error": error},
            )

    # 2. 风险分类
    try:
        level, reasons, preview, resource_version = _classify_for_proposal(
            db, context, WriteProposal(tool=proposal.tool, args=resolved_args)
        )
    except Exception as exc:  # noqa: BLE001
        error = f"规则层风险分类失败：{exc}"
        duration_ms = int((time.perf_counter() - started) * 1000)
        audit.record_tool_call(
            run_id=run_id,
            call_id=call_id,
            tool=proposal.tool,
            args=resolved_args,
            result={"ok": False, "error": error},
            ok=False,
            duration_ms=duration_ms,
        )
        return ProposalOutcome(
            tool=proposal.tool,
            status="failed",
            message=error,
            result_payload={"ok": False, "error": error},
        )

    # 3. 决策：低风险 + auto → 直接执行；高风险 / 需确认 → approval_required
    needs_approval = level in {RiskLevel.HIGH, RiskLevel.UNKNOWN} or (
        level == RiskLevel.LOW and not context.auto_execute_low_risk
    )
    if needs_approval:
        pending = _build_pending(
            run_id=run_id,
            call_id=call_id,
            tool=proposal.tool,
            args=resolved_args,
            level=level,
            reasons=reasons,
            preview=preview,
            resource_version=resource_version,
            model_name=model_name,
            model_id=model_id,
            session_id=context.session_id,
        )
        audit.record_approval_required(
            run_id=run_id,
            approval_id=pending["approval_id"],
            tool=proposal.tool,
            risk_level=level.value,
            reasons=reasons,
        )
        return ProposalOutcome(
            tool=proposal.tool,
            status="pending_confirmation",
            message="规则层产出写操作，等待用户确认",
            pending=pending,
            resolved_args=resolved_args,
        )

    # 4. 直接执行
    result = await _execute_proposal(
        db,
        context,
        WriteProposal(tool=proposal.tool, args=resolved_args),
    )
    duration_ms = int((time.perf_counter() - started) * 1000)
    audit.record_tool_call(
        run_id=run_id,
        call_id=call_id,
        tool=proposal.tool,
        args=resolved_args,
        result=result,
        ok=bool(result.get("ok", True)),
        duration_ms=duration_ms,
        approval_id=None,
        approval_decision="auto",
        automatic=True,
    )
    if not result.get("ok", True):
        return ProposalOutcome(
            tool=proposal.tool,
            status="failed",
            message=str(result.get("error", "执行失败")),
            result_payload=result,
            resolved_args=resolved_args,
        )
    return ProposalOutcome(
        tool=proposal.tool,
        status="completed",
        message=str(result.get("message", "已执行")),
        result_payload=result,
        resolved_args=resolved_args,
    )


def outcome_events(run_id: str, session_id: int, outcome: ProposalOutcome) -> list[str]:
    """把 ``ProposalOutcome`` 翻译为 SSE 事件列表（与主图同构）。"""
    events: list[str] = []
    call_id = f"{run_id}:{outcome.tool}"
    events.append(
        encode_sse_event(
            ToolStarted(
                event_id=f"{run_id}-tool-{outcome.tool}",
                run_id=run_id,
                call_id=call_id,
                tool=outcome.tool,
                summary=f"规则层直执：{outcome.tool}",
            )
        )
    )
    if outcome.status == "failed":
        payload = outcome.result_payload or {"ok": False, "error": outcome.message}
        events.append(
            encode_sse_event(
                ToolCompleted(
                    event_id=f"{run_id}-result-{outcome.tool}",
                    run_id=run_id,
                    call_id=call_id,
                    tool=outcome.tool,
                    result=dump_json(payload, default=str)[:2000],
                )
            )
        )
        events.append(
            encode_sse_event(
                ExecutionStatus(
                    event_id=f"{run_id}-exec-{outcome.tool}",
                    run_id=run_id,
                    session_id=session_id,
                    operator=outcome.tool,
                    status="failed",
                    call_id=call_id,
                    message=outcome.message,
                )
            )
        )
        return events

    if outcome.status == "pending_confirmation" and outcome.pending is not None:
        pending = outcome.pending
        events.append(
            encode_sse_event(
                ApprovalRequired(
                    event_id=f"{run_id}-approval-{outcome.tool}",
                    run_id=run_id,
                    session_id=session_id,
                    approval_id=pending["approval_id"],
                    operator=outcome.tool,
                    call_id=pending["call_id"],
                    risk_level=pending["risk_level"],
                    reasons=pending["reasons"],
                    preview=pending["preview"],
                )
            )
        )
        events.append(
            encode_sse_event(
                ExecutionStatus(
                    event_id=f"{run_id}-exec-{outcome.tool}",
                    run_id=run_id,
                    session_id=session_id,
                    operator=outcome.tool,
                    status="submitted",
                    call_id=pending["call_id"],
                    message="规则层已生成待审批操作",
                )
            )
        )
        return events

    # completed
    payload = outcome.result_payload or {"ok": True, "message": outcome.message}
    events.append(
        encode_sse_event(
            ToolCompleted(
                event_id=f"{run_id}-result-{outcome.tool}",
                run_id=run_id,
                call_id=call_id,
                tool=outcome.tool,
                result=dump_json(payload, default=str)[:2000],
            )
        )
    )
    events.append(
        encode_sse_event(
            ExecutionStatus(
                event_id=f"{run_id}-exec-{outcome.tool}",
                run_id=run_id,
                session_id=session_id,
                operator=outcome.tool,
                status="verified",
                call_id=call_id,
                message=outcome.message,
            )
        )
    )
    return events
