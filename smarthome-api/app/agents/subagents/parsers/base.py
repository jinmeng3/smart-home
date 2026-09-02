"""规则层解析器的公共契约：数据结构 + ``RuleParser`` 协议 + 解析上下文。

放在 ``parsers`` 包里而不是 ``rule_engine`` 里，是为了打破循环依赖：
``rule_engine`` 需要导入各个 parser，parser 又需要 ``RuleParseResult``。
``rule_engine`` 会重新导出这两个数据类，因此
``from app.agents.subagents.rule_engine import RuleParseResult`` 仍然可用。
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.agents.subagents.alias_index import AliasIndex
from app.agents.subagents.lexicon import RuleLexicon

# === 数据契约 ===


@dataclass(frozen=True, slots=True)
class WriteProposal:
    """规则层直接产出的可执行写提案。

    ``args`` **不含 device_id**——规则层不查家庭设备表，只产出"意图级"参数；
    真实设备由 ``rule_layer`` 按 ``RuleParseResult.entity_ref`` 反查后填充。
    """

    tool: str
    args: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RuleParseResult:
    """规则层解析结果。

    Attributes:
        matched: 是否成功解析为可执行意图。
        intent: 意图类别（``control`` / ``scene`` / ``query`` / ``schedule`` /
            ``composite``），未匹配时为空字符串。
        domain: 命中的领域标签，与 ``DOMAIN_KEYWORDS`` 的 key 对齐。
        confidence: 匹配置信度，区间 [0, 1]，< ``funnel_rule_confidence_low``
            视为不可用。
        action: 动作枚举（``on`` / ``off`` / ``set_temperature`` /
            ``set_position`` / ``trigger`` / ``query_state``）。
        entity: 目标实体类型（``light`` / ``air_conditioner`` / ``curtain`` /
            ``socket`` / ``device`` / ``scene`` / ``clock`` / ``temperature`` /
            ``humidity``），未识别时为空字符串。
        entity_ref: 解析出的实体引用文本（房间名 + 设备名 / 别名），用于在
            上下文中反查真实设备。
        params: 提取出的参数（如 ``{"temperature": 26}``）。
        response_text: 直接返回给用户的自然语言答案（用于「现在几点了」等
            简单查询场景）。
        write_proposals: 规则层直出的写提案列表；调用方仍需经 ``risk_check``
            审批。
        needs_clarification: 是否需要追问用户。
        clarification_prompt: 追问时建议使用的提示文本。
        elapsed_ms: 实际解析耗时（毫秒），用于性能监控。
    """

    matched: bool
    intent: str = ""
    domain: str = ""
    confidence: float = 0.0
    action: str = ""
    entity: str = ""
    entity_ref: str = ""
    params: dict[str, Any] = field(default_factory=dict)
    response_text: str = ""
    write_proposals: tuple[WriteProposal, ...] = ()
    needs_clarification: bool = False
    clarification_prompt: str = ""
    elapsed_ms: int = 0


# === 解析上下文 ===


@dataclass(frozen=True, slots=True)
class RuleContext:
    """一次 ``parse`` 调用期间传递给所有 parser 的只读上下文。

    ``elapsed_ms`` 是**可调用对象**而不是数值：parser 在构造结果时才取当前
    耗时，这样每条结果记录的都是"到本 parser 命中为止"的真实耗时。
    """

    text: str
    lexicon: RuleLexicon
    elapsed_ms: Callable[[], int]
    alias_index: AliasIndex | None = None
    conf_high: float = 0.97
    conf_mid: float = 0.85
    conf_low: float = 0.4


# === Parser 协议 ===


class RuleParser(Protocol):
    """规则层子解析器协议。

    实现方只需提供 ``name`` / ``priority`` / ``try_parse``：

    - ``name``：审计与埋点用的稳定标识；
    - ``priority``：**数值小者先执行**。约定 10 的倍数，方便在已有 parser
      之间插入自定义实现（如 15 插到 query=10 与 scene=20 之间）；
    - ``try_parse``：命中返回 ``RuleParseResult``，未命中返回 ``None``。
      **不得抛异常**——``RuleEngine`` 会兜住，但抛异常会让本次 parse 直接拒识。
    """

    name: str
    priority: int

    def try_parse(self, ctx: RuleContext) -> RuleParseResult | None: ...
