"""规则层引擎：调度各个子解析器，负责预算、别名热加载与拒识兜底。

职责边界
--------
本模块**只做调度**，不含任何业务词汇或抽取算法：

- 业务词表 → :mod:`app.agents.subagents.lexicon`
- 抽取算法 → :mod:`app.agents.subagents.parsers.extract`
- 各类意图 → :mod:`app.agents.subagents.parsers` 下的 ``*Parser``
- 别名反查 → :class:`app.agents.subagents.alias_index.AliasIndex`

扩展方式
--------
新增一类意图**不需要改本文件**：实现 ``RuleParser`` 协议后，
在 ``parsers.default_parsers()`` 里注册，或构造时传入 ``parsers=[...]``。

向后兼容
--------
``WriteProposal`` / ``RuleParseResult`` / ``AliasIndex`` 从本模块重新导出，
历史写法 ``from app.agents.subagents.rule_engine import RuleParseResult`` 仍可用。
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable

from app.agents.subagents.alias_index import AliasIndex
from app.agents.subagents.lexicon import RuleLexicon, get_lexicon
from app.agents.subagents.parsers import default_parsers
from app.agents.subagents.parsers.base import (
    RuleContext,
    RuleParser,
    RuleParseResult,
    WriteProposal,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)

__all__ = [
    "AliasIndex",
    "RuleEngine",
    "RuleParseResult",
    "RuleParser",
    "WriteProposal",
    "get_rule_engine",
    "reset_rule_engine",
]


# === 规则引擎 ===


class RuleEngine:
    """规则层意图解析器（调度器）。

    使用方式：

    .. code-block:: python

        engine = RuleEngine(alias_index=AliasIndex(household_id=1))
        result = engine.parse("打开客厅灯")
        if result.matched and result.confidence >= 0.95:
            for proposal in result.write_proposals:
                ...  # 交给 risk_check → approval

    线程安全说明：``parse`` 会写实例上的 ``_started_at``，**同一实例不可被
    多线程并发调用**。进程级单例 :func:`get_rule_engine` 在单线程事件循环
    （FastAPI 默认）下安全；多线程场景请每线程各持一个实例。
    """

    # 置信度档位：精确匹配 / 模糊匹配 / 拒识。
    _CONF_HIGH = 0.97
    _CONF_MID = 0.85
    _CONF_LOW = 0.4

    def __init__(
        self,
        *,
        alias_index: AliasIndex | None = None,
        alias_provider: Callable[[], AliasIndex | None] | None = None,
        parsers: list[RuleParser] | None = None,
        lexicon: RuleLexicon | None = None,
    ):
        # 静态别名索引：调用方在构造时绑定，后续不更新。
        self._alias_index = alias_index
        # 动态别名供应者：每次 ``parse`` 检查 ``version``，变化时换新。
        # 与 ``funnel_alias_hot_reload`` 配合使用——开启热加载时上层
        # 传一个返回当前 ``AliasIndex`` 的 callable（通常从设备 / 房间表
        # 重建），关闭时保持一次性绑定。
        self._alias_provider = alias_provider
        # 已持有的 provider 索引 ``version``，避免重复 setattr
        self._provider_version: int | None = None
        # 解析器列表，按 priority 升序执行；None 时用内置默认集合
        self._parsers = sorted(
            parsers if parsers is not None else default_parsers(),
            key=lambda parser: parser.priority,
        )
        # 词表：None 表示每次 parse 时取进程级缓存（支持 .env 扩充后重置生效）
        self._lexicon = lexicon
        # parse() 入口会重置该值，所有 _elapsed_ms 调用都相对此值
        self._started_at: float = 0.0

    # === 公开 API ===

    def parse(self, message: str) -> RuleParseResult:
        """同步解析；任何 parser 异常都被吞掉并降级为 ``matched=False``。

        性能预算：入口用 ``time.perf_counter`` 计时，**每个 parser 之前**都检查
        是否超出 ``funnel_rule_max_duration_ms``，超出立刻返回空匹配，由
        ``FunnelRouter`` 把请求抛给上层（上下文层 / LLM 兜底层）。
        """
        settings = get_settings()
        self._started_at = time.perf_counter()
        budget_ms = settings.funnel_rule_max_duration_ms
        # 入口先做别名热加载检查（与解析路径解耦）
        self._refresh_alias_index()

        text = (message or "").strip()
        if not text:
            return self._unmatched()

        lexicon = self._lexicon or get_lexicon()

        # 复合意图检测：含连接词 / 决策词时规则层不能拍板，一律交兜底层。
        # 避免「我睡觉了，顺便看看明天天气决定要不要开加湿器」被误识别为
        # 「睡觉了」场景而直接执行。
        if self._is_composite_intent(text, lexicon):
            return self._unmatched(intent="composite")

        ctx = RuleContext(
            text=text,
            lexicon=lexicon,
            elapsed_ms=self._elapsed_ms,
            alias_index=self._alias_index,
            conf_high=self._CONF_HIGH,
            conf_mid=self._CONF_MID,
            conf_low=self._CONF_LOW,
        )

        for parser in self._parsers:
            if self._over_budget(budget_ms):
                # 预算耗尽：已跑过的 parser 都没命中，剩下的更贵，直接放弃
                logger.debug(
                    "规则层预算耗尽，放弃剩余解析器：next=%s elapsed_ms=%s budget_ms=%s",
                    parser.name,
                    self._elapsed_ms(),
                    budget_ms,
                )
                return self._unmatched()
            result = self._run_parser(parser, ctx)
            if result is not None:
                return result

        # 全部 parser 都未命中 → 拒识
        return self._unmatched()

    # === 内部：调度 ===

    def _run_parser(
        self, parser: RuleParser, ctx: RuleContext
    ) -> RuleParseResult | None:
        """执行单个 parser；异常不外泄，仅记录日志并视为未命中。"""
        try:
            return parser.try_parse(ctx)
        except Exception:  # 单个解析器故障不应让整层拒绍服务
            logger.warning(
                "规则层解析器异常，已跳过：parser=%s", parser.name, exc_info=True
            )
            return None

    @staticmethod
    def _is_composite_intent(text: str, lexicon: RuleLexicon) -> bool:
        """检测「复合 / 跨域 / 决策型」意图，命中则让规则层拒识。

        信号来自 ``lexicon.composite_signals``（并列连接词，如「顺便」「还有」）
        与 ``lexicon.decision_signals``（决策词，如「决定」「要不要」）。
        """
        if not text:
            return False
        return any(signal in text for signal in lexicon.all_composite_signals)

    def _unmatched(self, *, intent: str = "") -> RuleParseResult:
        """构造拒识结果，统一带上当前耗时便于埋点。"""
        return RuleParseResult(
            matched=False,
            intent=intent,
            domain="",
            confidence=0.0,
            elapsed_ms=self._elapsed_ms(),
        )

    # === 内部：别名热加载 ===

    def _refresh_alias_index(self) -> None:
        """调用 ``alias_provider`` 检查 ``version``；变化则换新 ``_alias_index``。

        关闭热加载（``funnel_alias_hot_reload=False``）时直接返回，保持
        一次性绑定的现有行为。
        """
        if self._alias_provider is None:
            return
        if not get_settings().funnel_alias_hot_reload:
            return
        current = self._alias_provider()
        if current is None:
            return
        if self._provider_version is None:
            # 首次调用：直接绑定并记录 version
            self._alias_index = current
            self._provider_version = current.version
            return
        if current.version != self._provider_version:
            self._alias_index = current
            self._provider_version = current.version

    # === 内部：预算 ===

    def _elapsed_ms(self) -> int:
        return int((time.perf_counter() - self._started_at) * 1000)

    def _over_budget(self, budget_ms: int) -> bool:
        return self._elapsed_ms() > budget_ms


# === 便捷入口 ===


_default_engine: RuleEngine | None = None


def get_rule_engine() -> RuleEngine:
    """获取进程级单例 ``RuleEngine``。"""
    global _default_engine
    if _default_engine is None:
        _default_engine = RuleEngine()
    return _default_engine


def reset_rule_engine() -> None:
    """清空单例（测试 / 更换解析器集合后调用）。"""
    global _default_engine
    _default_engine = None
