"""规则层直接执行器（Rule Layer Direct Executor）单元测试。

覆盖：

- 简单查询：直接返回缓存 / 现查结果，0 Token；
- 写路径：低风险 + auto → 直接执行；高风险 → approval_required；
- 找不到设备 → 失败事件 + error；
- SSE 事件序列与 LLM 主图同构（前端解析器可复用）。
"""

import json
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock

import anyio

from app.agents.context import AgentContext
from app.agents.subagents.rule_engine import RuleParseResult, WriteProposal
from app.agents.subagents.rule_layer import (
    ProposalOutcome,
    _resolve_device,
    _split_room_from_entity_ref,
    execute_rule_layer,
    outcome_events,
)


def _as_context(**fields) -> AgentContext:
    """构造一个看似 ``AgentContext`` 的 ``SimpleNamespace``。

    生产代码 ``execute_rule_layer(context: AgentContext, ...)`` 显式声明
    了类型；测试需要 duck-typed 上下文以避免依赖完整初始化。``cast`` 在
    运行时是零成本，只是告诉类型检查器“知道这里是 duck-typed”。
    """
    return cast(AgentContext, SimpleNamespace(**fields))

# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------


def _parse_sse_event(event_str: str) -> dict:
    """把 ``event: name\\ndata: {json}\\n\\n`` 解析为 dict。"""
    lines = event_str.strip().split("\n")
    assert lines[0].startswith("event: "), f"非法 SSE 事件: {event_str!r}"
    event_name = lines[0][len("event: ") :]
    data_line = lines[1]
    assert data_line.startswith("data: ")
    payload = json.loads(data_line[len("data: ") :])
    payload["_event"] = event_name
    return payload


async def _collect_events_async(agen):
    """从 async generator 收集全部事件。"""
    events = []
    aiter = agen.__aiter__()
    while True:
        try:
            event = await aiter.__anext__()
            events.append(event)
        except StopAsyncIteration:
            break
    return events


def _collect_events(agen):
    """从 sync 上下文收集 async generator 产生的所有事件。

    为 ``test_no_proposals_emits_error`` 这类需要 sync 测试函数包装的
    场景提供便捷包装。
    """
    return anyio.run(_collect_events_async, agen)


def _make_safe_db(*, scalar_returns: object = None) -> MagicMock:
    """构造一个能让 ``execute_rule_layer`` 完整跑通的 MagicMock db。

    设计约束（调用顺序很重要）：

    1. ``rate_limiter.check_daily_budget`` 调 ``db.scalar(...)`` 查今日
       已用 token，再与 ``agent_daily_budget_tokens``（int）比较。若
       ``db.scalar`` 返回 MagicMock，会出现 ``MagicMock >= int`` TypeError。
       → 默认 ``scalar_returns=None`` 可让函数 early-return
       （``if result is not None and result >= ...`` 在 result=None 时跳过）。
    2. ``usage.store_usage`` 也调 ``db.scalar(select(AgentUsage)...)``，
       若返回 MagicMock 则走 else 分支 ``usage.input_tokens += ...``，会
       AttributeError。
       → 同样默认 ``None`` 会让 ``is_new_run=True`` 走新建分支。
    3. ``_resolve_device`` 走 ``db.scalar(select(Device)...)``，返回 ``None``
       表示未找到设备。默认 ``None`` 行为正好一致。

    如需模拟“今日已用 N token”这类场景，调用方传入 ``scalar_returns=N``。
    """
    db = MagicMock()
    db.scalar.return_value = scalar_returns
    db.scalars.return_value.all.return_value = []
    db.add = MagicMock()
    db.commit = MagicMock()
    db.rollback = MagicMock()
    db.get_bind = MagicMock(return_value=SimpleNamespace(dialect=SimpleNamespace(name="sqlite")))
    return db


# ---------------------------------------------------------------------------
# 内部工具
# ---------------------------------------------------------------------------


class TestRoomSplit:
    def test_split_room_from_entity(self):
        assert _split_room_from_entity_ref("客厅灯", room_hint="") == "客厅"
        assert _split_room_from_entity_ref("卧室空调", room_hint="") == "卧室"
        assert _split_room_from_entity_ref("窗帘", room_hint="") == ""

    def test_room_hint_overrides_split(self):
        assert _split_room_from_entity_ref("客厅灯", room_hint="主卧") == "主卧"


class TestResolveDevice:
    def test_resolve_by_exact_name(self):
        device = SimpleNamespace(id=42, name="客厅灯", type="light", household_id=1)
        db = MagicMock()
        db.scalar.return_value = device
        ctx = _as_context(household_id=1)
        result = _resolve_device(
            db, ctx, entity_type="light", entity_ref="客厅灯", room=""
        )
        assert result is device
        db.scalar.assert_called()

    def test_resolve_returns_none_when_not_found(self):
        db = MagicMock()
        db.scalar.return_value = None
        db.scalars.return_value.all.return_value = []
        ctx = _as_context(household_id=1)
        result = _resolve_device(
            db, ctx, entity_type="light", entity_ref="不存在的设备", room=""
        )
        assert result is None


# ---------------------------------------------------------------------------
# 简单查询
# ---------------------------------------------------------------------------


class TestSimpleQuery:
    def test_query_clock_emits_message_and_completed(self):
        anyio.run(self._test_query_clock_emits_message_and_completed)

    async def _test_query_clock_emits_message_and_completed(self):
        rule = RuleParseResult(
            matched=True,
            intent="query",
            domain="device",
            confidence=0.97,
            action="query_state",
            entity="clock",
        )
        agen = execute_rule_layer(
            context=_as_context(
                user_id=1,
                household_id=1,
                session_id=1,
                auto_execute_low_risk=False,
                confirm_high_risk=True,
            ),
            household_name="家",
            message="现在几点了",
            model_name="rule-layer",
            model_id=None,
            db=_make_safe_db(),
            rule_result=rule,
        )
        events = await _collect_events_async(agen)
        parsed = [_parse_sse_event(e) for e in events]
        kinds = [e["_event"] for e in parsed]
        assert "run_started" in kinds
        assert "message_delta" in kinds
        assert "run_completed" in kinds
        msg = next(e for e in parsed if e["_event"] == "message_delta")
        assert "本地时间" in msg["content"]


# ---------------------------------------------------------------------------
# 写提案
# ---------------------------------------------------------------------------


class TestWriteProposals:
    def test_failed_when_device_not_found(self):
        anyio.run(self._test_failed_when_device_not_found)

    async def _test_failed_when_device_not_found(self):
        rule = RuleParseResult(
            matched=True,
            intent="control",
            domain="device",
            confidence=0.97,
            action="on",
            entity="light",
            entity_ref="不存在的灯",
            write_proposals=(
                WriteProposal(tool="set_device_power", args={"power": "on"}),
            ),
        )
        # DB 返回空（找不到设备）；同时用 ``_make_safe_db`` 避免 rate_limiter
        # 在 ``db.scalar`` 返回 MagicMock 时出现 ``MagicMock >= int`` TypeError。
        db = _make_safe_db()
        db.scalar.return_value = None
        db.scalars.return_value.all.return_value = []

        agen = execute_rule_layer(
            context=_as_context(
                user_id=1,
                household_id=1,
                session_id=1,
                auto_execute_low_risk=True,
                confirm_high_risk=False,
            ),
            household_name="家",
            message="打开不存在的灯",
            model_name="rule-layer",
            model_id=None,
            db=db,
            rule_result=rule,
        )
        events = await _collect_events_async(agen)
        parsed = [_parse_sse_event(e) for e in events]
        kinds = [e["_event"] for e in parsed]
        assert "tool_started" in kinds
        assert "tool_completed" in kinds
        # 至少有一个 failed 状态的 execution_status
        failed = [
            e
            for e in parsed
            if e["_event"] == "execution_status" and e.get("status") == "failed"
        ]
        assert failed
        # 最终 run_completed 是 failed
        completed = next(e for e in parsed if e["_event"] == "run_completed")
        assert completed["status"] == "failed"


# ---------------------------------------------------------------------------
# outcome_events 翻译
# ---------------------------------------------------------------------------


class TestOutcomeEvents:
    def test_completed_outcome_emits_verified(self):
        outcome = ProposalOutcome(
            tool="set_device_power",
            status="completed",
            message="设备已开机",
            result_payload={"ok": True, "message": "设备「客厅灯」已开机"},
            resolved_args={"device_id": 42, "power": "on"},
        )
        events = outcome_events("run-test", 1, outcome)
        parsed = [_parse_sse_event(e) for e in events]
        kinds = [e["_event"] for e in parsed]
        assert "tool_started" in kinds
        assert "tool_completed" in kinds
        assert "execution_status" in kinds
        exec_status = next(e for e in parsed if e["_event"] == "execution_status")
        assert exec_status["status"] == "verified"
        assert exec_status["operator"] == "set_device_power"

    def test_failed_outcome_emits_failed_status(self):
        outcome = ProposalOutcome(
            tool="set_device_power",
            status="failed",
            message="未找到设备",
            result_payload={"ok": False, "error": "未找到设备"},
        )
        events = outcome_events("run-test", 1, outcome)
        parsed = [_parse_sse_event(e) for e in events]
        exec_status = next(e for e in parsed if e["_event"] == "execution_status")
        assert exec_status["status"] == "failed"
        assert "未找到设备" in exec_status["message"]

    def test_pending_outcome_emits_approval_required(self):
        outcome = ProposalOutcome(
            tool="execute_scene",
            status="pending_confirmation",
            message="等待确认",
            pending={
                "approval_id": "run-test:0",
                "run_id": "run-test",
                "session_id": 1,
                "call_id": "call-0",
                "tool": "execute_scene",
                "args": {"scene_id": "sleep"},
                "risk_level": "high",
                "reasons": ["涉及高风险设备"],
                "preview": {},
            },
        )
        events = outcome_events("run-test", 1, outcome)
        parsed = [_parse_sse_event(e) for e in events]
        kinds = [e["_event"] for e in parsed]
        assert "approval_required" in kinds
        approval = next(e for e in parsed if e["_event"] == "approval_required")
        assert approval["risk_level"] == "high"
        assert approval["operator"] == "execute_scene"


# ---------------------------------------------------------------------------
# 拒识 / 空提案
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_no_proposals_emits_error(self):
        rule = RuleParseResult(
            matched=True,
            intent="control",
            domain="device",
            confidence=0.97,
            action="on",
        )
        agen = execute_rule_layer(
            context=_as_context(
                user_id=1,
                household_id=1,
                session_id=1,
                auto_execute_low_risk=False,
                confirm_high_risk=True,
            ),
            household_name="家",
            message="",
            model_name="rule-layer",
            model_id=None,
            db=_make_safe_db(),
            rule_result=rule,
        )
        events = _collect_events(agen)
        parsed = [_parse_sse_event(e) for e in events]
        kinds = [e["_event"] for e in parsed]
        assert "error" in kinds
        err = next(e for e in parsed if e["_event"] == "error")
        assert err["code"] == "AGENT_RULE_NO_PROPOSAL"
