"""漏斗路由器（Funnel Router）单元测试。"""

import pytest
from app.agents.subagents.funnel_router import (
    LAYER_CONTEXT,
    LAYER_FALLBACK,
    LAYER_RULE,
    FunnelRouter,
    SessionState,
    get_funnel_router,
    reset_funnel_router,
)
from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _restore_settings():
    """避免单测修改全局 settings。"""
    get_settings()
    yield
    # settings 由 lru_cache 包装；本测试只读，不修改


# ---------------------------------------------------------------------------
# 路由分流
# ---------------------------------------------------------------------------


class TestRouting:
    def test_high_confidence_control_goes_to_rule_layer(self):
        router = FunnelRouter()
        result = router.route("打开客厅灯")
        assert result.layer == LAYER_RULE
        assert result.rule_result is not None
        assert result.confidence >= 0.95
        assert len(result.write_proposals) == 1
        assert result.write_proposals[0].tool == "set_device_power"

    def test_scene_goes_to_rule_layer(self):
        router = FunnelRouter()
        result = router.route("我回来了")
        assert result.layer == LAYER_RULE
        assert result.write_proposals[0].tool == "execute_scene"

    def test_query_goes_to_rule_layer(self):
        router = FunnelRouter()
        result = router.route("现在几点了")
        assert result.layer == LAYER_RULE
        assert result.rule_result.intent == "query"

    def test_pronoun_routes_to_context(self):
        router = FunnelRouter()
        result = router.route("那卧室呢？")
        assert result.layer == LAYER_CONTEXT
        assert "活动对话框" in result.explanation or "指代词" in result.explanation

    def test_relative_control_routes_to_context(self):
        router = FunnelRouter()
        result = router.route("再亮一点")
        assert result.layer == LAYER_CONTEXT

    def test_unmatched_routes_to_fallback(self):
        router = FunnelRouter()
        result = router.route("我睡觉了，顺便看看明天天气决定要不要开加湿器")
        # 复合跨域：规则层不会精确匹配，走兜底层
        assert result.layer == LAYER_FALLBACK

    def test_active_dialog_routes_to_context(self):
        router = FunnelRouter()
        state = SessionState(has_active_dialog=True)
        result = router.route("帮我定个闹钟", state)
        assert result.layer == LAYER_CONTEXT

    def test_empty_message_falls_through(self):
        router = FunnelRouter()
        result = router.route("")
        assert result.layer == LAYER_FALLBACK


# ---------------------------------------------------------------------------
# 禁用漏斗
# ---------------------------------------------------------------------------


class TestFunnelDisabled:
    def test_funnel_disabled_all_to_fallback(self, monkeypatch):
        from app.agents.subagents import funnel_router as module

        class _StubSettings:
            funnel_enabled = False
            funnel_rule_confidence_high = 0.95
            funnel_rule_confidence_low = 0.8

        monkeypatch.setattr(module, "get_settings", lambda: _StubSettings())
        router = FunnelRouter()
        result = router.route("打开客厅灯")
        assert result.layer == LAYER_FALLBACK
        assert "funnel_disabled" in result.explanation


# ---------------------------------------------------------------------------
# 信号优先级
# ---------------------------------------------------------------------------


class TestSignalPriority:
    def test_explanation_contains_reason(self):
        router = FunnelRouter()
        result = router.route("打开客厅灯")
        assert "规则层" in result.explanation

    def test_debug_carries_settings(self):
        router = FunnelRouter()
        result = router.route("打开客厅灯")
        assert "rule" in result.debug
        assert "settings" in result.debug
        assert result.debug["rule"]["matched"] is True

    def test_unmatched_debug_has_fallback_reason(self):
        router = FunnelRouter()
        result = router.route("完全无法理解的奇怪复合长尾指令 xyzzy")
        assert "fallback" in result.debug
        assert result.debug["fallback"]["reason"] == "no_rule_match"


# ---------------------------------------------------------------------------
# 单例
# ---------------------------------------------------------------------------


def test_get_funnel_router_singleton():
    reset_funnel_router()
    a = get_funnel_router()
    b = get_funnel_router()
    assert a is b
    reset_funnel_router()
