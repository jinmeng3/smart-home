from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.agents.subagents.router import (
    resolve_delegated_domain,
    route_intent,
)
from app.agents.subagents.rule_engine import (
    AliasIndex,
    RuleEngine,
    RuleParseResult,
    WriteProposal,
    get_rule_engine,
)
from app.core.config import get_settings

# 第二层 / 第三层的占位标签，便于上层按层做埋点和指标。
LAYER_RULE = "rule"
LAYER_CONTEXT = "context"
LAYER_FALLBACK = "fallback"
LAYER_DIRECT = "direct"  # 极简路径：直接跳过 LLM，仅产出文本 / 状态


# 指代词 / 相对控制关键词：第二层（上下文层）的入口信号。
_PRONOUNS = (
    "那",
    "它",
    "这个",
    "那个",
    "这些",
    "那些",
    "这里",
    "那里",
    "这",
    "那",
    "刚才",
    "之前",
    "上一",
    "再",
    "又",
    "继续",
)
_RELATIVE_KEYWORDS = (
    "再亮",
    "再暗",
    "再大",
    "再小",
    "再高",
    "再低",
    "再暖",
    "再冷",
    "再快",
    "再慢",
    "大一点",
    "小一点",
    "高一点",
    "低一点",
    "暖一点",
    "冷一点",
    "亮一点",
    "暗一点",
    "声音大",
    "声音小",
    "音量大",
    "音量小",
    "上次的",
    "刚才的",
)


@dataclass(frozen=True, slots=True)
class SessionState:
    """路由器所需的会话视图。

    实际项目里可由会话树 / checkpointer 重建；当前仅承载 P0 必需的字段：

    - ``session_id``：用于审计 / 缓存
    - ``household_id``：用于别名索引与设备反查
    - ``has_active_dialog``：是否有未完成的多轮槽位
    - ``last_intent``：上一轮意图（指代消解时由上下文层继承）
    """

    session_id: int = 0
    household_id: int = 0
    has_active_dialog: bool = False
    last_intent: str = ""
    last_entity_type: str = ""


@dataclass(frozen=True, slots=True)
class RouteResult:
    """路由器决策结果。

    调用方（runner）按 ``layer`` 决定下一步行为：

    - ``LAYER_RULE`` / ``LAYER_DIRECT`` → 读取 ``write_proposals``，走 ``risk_check``
    - ``LAYER_FALLBACK`` → 调用现有 ``run_agent_body`` 走主图
    - ``LAYER_CONTEXT`` → 上下文层（**P1，本期回退到 LAYER_FALLBACK**）

    ``confidence`` 透传规则层结果，便于埋点；``explanation`` 给出可读理由，
    方便前端在调试模式展示。
    """

    layer: str
    confidence: float = 0.0
    rule_result: RuleParseResult | None = None
    fallback_domain: str | None = None
    write_proposals: tuple[WriteProposal, ...] = ()
    clarification_prompt: str = ""
    explanation: str = ""
    debug: dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 路由器
# ---------------------------------------------------------------------------


class FunnelRouter:
    """漏斗式分层路由。

    依赖：

    - ``RuleEngine``：规则层解析
    - ``AliasIndex``：可选的别名倒排索引（家庭级）
    - 会话状态（``SessionState``）：第二层判定的输入
    """

    def __init__(
        self,
        *,
        rule_engine: RuleEngine | None = None,
        alias_index: AliasIndex | None = None,
    ):
        self._rule_engine = rule_engine or get_rule_engine()
        self._alias_index = alias_index

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

    def route(
        self, user_input: str, session_state: SessionState | None = None
    ) -> RouteResult:
        """对一次用户输入做路由决策。永不抛异常（拒识走兜底层）。"""
        settings = get_settings()
        if not settings.funnel_enabled:
            # 漏斗整体关闭 → 全部走兜底层（保持旧行为）
            return self._fallback_result(user_input, reason="funnel_disabled")

        state = session_state or SessionState()
        debug: dict[str, Any] = {
            "funnel_enabled": True,
            "settings": {
                "rule_confidence_high": settings.funnel_rule_confidence_high,
                "rule_confidence_low": settings.funnel_rule_confidence_low,
            },
        }

        # 1. 规则层解析
        rule_result = self._rule_engine.parse(user_input)
        debug["rule"] = {
            "matched": rule_result.matched,
            "confidence": rule_result.confidence,
            "elapsed_ms": rule_result.elapsed_ms,
            "intent": rule_result.intent,
            "domain": rule_result.domain,
            "action": rule_result.action,
        }

        # 2. 信号判定
        if rule_result.matched:
            if rule_result.confidence >= settings.funnel_rule_confidence_high:
                return RouteResult(
                    layer=LAYER_RULE,
                    confidence=rule_result.confidence,
                    rule_result=rule_result,
                    write_proposals=rule_result.write_proposals,
                    clarification_prompt=rule_result.clarification_prompt,
                    explanation="规则层精确命中",
                    debug=debug,
                )
            if rule_result.confidence >= settings.funnel_rule_confidence_low:
                # 模糊命中：进入第二层（上下文层）。runner 会先尝试上下文层消解；
                # 若仍不确定，则把「追问」透传给上层（LLM）以自然语言确认。
                return RouteResult(
                    layer=LAYER_CONTEXT,
                    confidence=rule_result.confidence,
                    rule_result=rule_result,
                    clarification_prompt=rule_result.clarification_prompt
                    or "请补充更明确的目标",
                    explanation="规则层模糊命中 → 上下文层（未命中再回退 LLM 兜底）",
                    debug=debug,
                )

        # 3. 多轮 / 指代检测：第二层（上下文层）入口
        if state.has_active_dialog or self._has_pronoun(user_input):
            return RouteResult(
                layer=LAYER_CONTEXT,
                confidence=rule_result.confidence if rule_result.matched else 0.0,
                rule_result=rule_result if rule_result.matched else None,
                explanation=(
                    "存在活动对话框 / 指代词 → 上下文层（未命中再回退 LLM 兜底）"
                ),
                debug=debug,
            )

        # 4. 兜底层：现有主图 / 子 Agent 委托
        return self._fallback_result(user_input, reason="no_rule_match", debug=debug)

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------

    def _fallback_result(
        self,
        user_input: str,
        *,
        reason: str,
        debug: dict[str, Any] | None = None,
    ) -> RouteResult:
        domain = resolve_delegated_domain(user_input)
        merged_debug = dict(debug or {})
        merged_debug["fallback"] = {
            "reason": reason,
            "delegated_domain": domain,
            "route_tags": route_intent(user_input),
        }
        return RouteResult(
            layer=LAYER_FALLBACK,
            confidence=0.0,
            fallback_domain=domain,
            explanation=f"兜底层：{reason}",
            debug=merged_debug,
        )

    @staticmethod
    def _has_pronoun(text: str) -> bool:
        if not text:
            return False
        if any(p in text for p in _PRONOUNS):
            return True
        return any(kw in text for kw in _RELATIVE_KEYWORDS)


# ---------------------------------------------------------------------------
# 进程级单例
# ---------------------------------------------------------------------------


_default_router: FunnelRouter | None = None


def get_funnel_router() -> FunnelRouter:
    """获取进程级单例 ``FunnelRouter``。"""
    global _default_router
    if _default_router is None:
        _default_router = FunnelRouter()
    return _default_router


def reset_funnel_router() -> None:
    """重置单例（测试 / 热加载别名为新家庭时使用）。"""
    global _default_router
    _default_router = None
