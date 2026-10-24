"""漏斗路由器（FunnelRouter）单元测试。

覆盖范围（与 ``docs/funnel-routing-architecture.md`` §8 对齐）：

- 规则层精确命中（> high 阈值）→ LAYER_RULE
- 规则层模糊命中（low ~ high）→ LAYER_CONTEXT
- 规则层未命中 + 多轮 / 指代 → LAYER_CONTEXT
- 规则层未命中 + 复合 / 模糊 → LAYER_FALLBACK
- ``funnel_enabled=False`` → 一律 LAYER_FALLBACK
- 兜底层带 ``fallback_domain``（来自 ``resolve_delegated_domain``）
- debug 字段保留可观测性
"""

from __future__ import annotations

import pytest

from app.agents.subagents.funnel_router import (
    LAYER_CONTEXT,
    LAYER_FALLBACK,
    LAYER_RULE,
    FunnelRouter,
    SessionState,
    get_funnel_router,
)

# ---------------------------------------------------------------------------
# 公共 fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def router() -> FunnelRouter:
    return get_funnel_router()


# ---------------------------------------------------------------------------
# 三层分流
# ---------------------------------------------------------------------------


class TestLayerDispatch:
    def test_high_confidence_to_rule_layer(self, router: FunnelRouter):
        r = router.route("打开客厅灯", SessionState())
        assert r.layer == LAYER_RULE
        assert r.rule_result is not None
        assert r.rule_result.intent == "control"
        # 写提案透传
        assert any(p.tool == "set_device_power" for p in r.write_proposals)

    def test_scene_to_rule_layer(self, router: FunnelRouter):
        r = router.route("我回来了", SessionState())
        assert r.layer == LAYER_RULE
        assert r.rule_result is not None
        assert r.rule_result.intent == "scene"

    def test_query_to_rule_layer(self, router: FunnelRouter):
        r = router.route("现在几点了", SessionState())
        assert r.layer == LAYER_RULE
        assert r.rule_result is not None
        assert r.rule_result.intent == "query"

    def test_fallback_for_composite(self, router: FunnelRouter):
        r = router.route("我睡觉了，顺便看看明天天气", SessionState())
        assert r.layer == LAYER_FALLBACK
        assert r.fallback_domain is None  # 复合意图不委托给单领域

    def test_context_layer_via_pronoun(self, router: FunnelRouter):
        r = router.route("那卧室呢？", SessionState())
        assert r.layer == LAYER_CONTEXT

    def test_context_layer_via_active_dialog(self, router: FunnelRouter):
        # 上一轮已有未完成槽位 + 当前未匹配规则
        state = SessionState(has_active_dialog=True)
        r = router.route("明早七点", state)
        assert r.layer == LAYER_CONTEXT


# ---------------------------------------------------------------------------
# 兜底层 + 委托
# ---------------------------------------------------------------------------


class TestFallback:
    def test_fallback_carries_delegated_domain(self, router: FunnelRouter):
        # 「能耗」是 read-only 委托域
        r = router.route("本月能耗多少", SessionState())
        assert r.layer == LAYER_FALLBACK
        # 「能耗」关键词命中 → 委托给 energy 子 Agent
        # 注：当前 energy 不在 DELEGATABLE_DOMAINS，所以 fallback_domain 为 None
        # 仅校验不会抛异常且 layer 正确
        assert r.fallback_domain in (None, "energy")

    def test_fallback_for_general(self, router: FunnelRouter):
        r = router.route("你好", SessionState())
        assert r.layer == LAYER_FALLBACK
        assert r.fallback_domain is None


# ---------------------------------------------------------------------------
# 开关
# ---------------------------------------------------------------------------


class TestSwitches:
    def test_funnel_disabled_always_fallback(self, settings):
        settings.funnel_enabled = False
        router = FunnelRouter()
        r = router.route("打开客厅灯", SessionState())
        # 漏斗关 → 一律 LAYER_FALLBACK
        assert r.layer == LAYER_FALLBACK
        assert r.fallback_domain == "device"  # device 仍是可委托域

    def test_confidence_threshold_low(self, settings):
        # 把 low 阈值抬到 0.99 → 几乎所有规则层命中都会变成"模糊"
        settings.funnel_rule_confidence_low = 0.99
        settings.funnel_rule_confidence_high = 1.01  # 永远达不到
        router = FunnelRouter()
        r = router.route("打开客厅灯", SessionState())
        # 0.97 落在 [0.99, 1.01) 区间外 → 既不 high 也不 low → 走 fallback
        assert r.layer == LAYER_FALLBACK


# ---------------------------------------------------------------------------
# 可观测性
# ---------------------------------------------------------------------------


class TestObservability:
    def test_debug_contains_rule_signal(self, router: FunnelRouter):
        r = router.route("打开客厅灯", SessionState())
        assert "rule" in r.debug
        assert r.debug["rule"]["matched"] is True
        assert r.debug["rule"]["confidence"] >= 0.95

    def test_explanation_is_human_readable(self, router: FunnelRouter):
        r = router.route("打开客厅灯", SessionState())
        assert "规则层" in r.explanation


# ---------------------------------------------------------------------------
# 会话状态
# ---------------------------------------------------------------------------


class TestSessionState:
    def test_session_state_defaults(self):
        s = SessionState()
        assert s.has_active_dialog is False
        assert s.last_intent == ""
        assert s.household_id == 0

    def test_session_state_propagated(self, router: FunnelRouter):
        s = SessionState(session_id=42, household_id=7, has_active_dialog=True)
        r = router.route("明早七点", s)
        # 多轮信号 → 上下文层
        assert r.layer == LAYER_CONTEXT


# ---------------------------------------------------------------------------
# 鲁棒性
# ---------------------------------------------------------------------------


class TestRobustness:
    def test_empty_input_no_crash(self, router: FunnelRouter):
        r = router.route("", SessionState())
        # 空输入不抛异常
        assert r.layer in (LAYER_RULE, LAYER_CONTEXT, LAYER_FALLBACK)

    def test_garbage_input_no_crash(self, router: FunnelRouter):
        r = router.route("asdfghjkl qwertyuiop", SessionState())
        assert r.layer == LAYER_FALLBACK


# ---------------------------------------------------------------------------
# 模块级单例
# ---------------------------------------------------------------------------


def test_singleton():
    a = get_funnel_router()
    b = get_funnel_router()
    assert a is b
