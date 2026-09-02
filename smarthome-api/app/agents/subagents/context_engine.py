from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.agents.subagents.embedding import (
    EmbeddingUnavailable,
    SemanticEmbedder,
    cosine_similarity,
    get_embedder,
)
from app.agents.subagents.lexicon import get_lexicon
from app.agents.subagents.parsers.extract import extract_room
from app.agents.subagents.rule_engine import (
    RuleEngine,
    RuleParseResult,
    get_rule_engine,
)
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# 指代前缀 / 房间级省略表达（「那卧室呢」「它呢」「这家灯」等）。
_PRONOUN_PREFIXES = (
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
)
# 明确的动作 verb 表：命中任一即视为「非指代」请求，交给规则层 / 兜底层。
# 词表可通过 ``.env`` 扩充，因此在函数里惰性取，不能在模块加载时固化。
def _action_patterns():
    lexicon = get_lexicon()
    return (
        lexicon.turn_on_re,
        lexicon.turn_off_re,
        lexicon.set_temp_re,
        lexicon.set_position_re,
        lexicon.query_state_re,
    )

# 相对 / 增量控制，需要设备实时状态，本层无法安全解题。
_RELATIVE_CONTROL = (
    "大一点",
    "小一点",
    "高一点",
    "低一点",
    "暖一点",
    "冷一点",
    "亮一点",
    "暗一点",
    "再大",
    "再小",
    "再高",
    "再低",
    "再暖",
    "再冷",
    "再亮",
    "再暗",
    "声音大",
    "声音小",
    "音量大",
    "音量小",
)

# 继承结果统一按「明确、可直接执行」置信度给出（>= funnel_rule_confidence_high）。
_CONF_INHERIT = 0.96


@dataclass(frozen=True, slots=True)
class ContextResolution:
    """上下文层消解结果。

    调用方（runner）按 ``matched`` 决定下一步：

    - ``matched=True`` 且 ``rule_result`` 非空 → 交由 ``execute_rule_layer`` 执行
    - ``matched=False`` → 归还兜底层（LLM 主图）

    ``needs_fallback`` 与 ``matched`` 保持一致：未消解即示意上层接管。
    """

    matched: bool
    rule_result: RuleParseResult | None = None
    needs_fallback: bool = False
    explanation: str = ""


class ContextEngine:
    """上下文层确定性消解器。

    使用方式：

    .. code-block:: python

        engine = get_context_engine()
        res = engine.resolve("那卧室呢？", previous_user_message="客厅温度多少")
        if res.matched and res.rule_result is not None:
            # 交由 execute_rule_layer 执行，写操作仍走 risk_check
            ...
    """

    def __init__(
        self,
        *,
        rule_engine: RuleEngine | None = None,
        embedder: SemanticEmbedder | EmbeddingUnavailable | None = None,
    ):
        self._rule_engine = rule_engine or get_rule_engine()
        # 未传时按需懒加载；依赖缺失 / 未启用时会拿到 ``EmbeddingUnavailable``，
        # 所有语义路径会安全降级为现有启发式逻辑。
        self._embedder = embedder if embedder is not None else get_embedder()

    # === 公开 API ===

    def resolve(
        self,
        message: str,
        *,
        previous_user_message: str = "",
    ) -> ContextResolution:
        """对一次上下文层请求做多轮 / 指代消解。永不抛异常。"""
        try:
            return self._resolve_inner(message, previous_user_message or "")
        except Exception:  # noqa: BLE001  # 消解失败一律归还兜底层
            return ContextResolution(
                matched=False,
                needs_fallback=True,
                explanation="上下文层消解异常 → 兜底层",
            )

    # === 内部实现 ===

    def _resolve_inner(
        self, message: str, previous_user_message: str
    ) -> ContextResolution:
        text = (message or "").strip()
        if not text:
            return ContextResolution(
                matched=False, needs_fallback=True, explanation="空输入 → 兜底层"
            )

        # 相对控制：需要设备实时状态，本层不处理
        if self._is_relative_control(text):
            return ContextResolution(
                matched=False,
                needs_fallback=True,
                explanation="相对控制需设备状态 → 兜底层",
            )

        # 实体引用型指代（无动作 verb，仅有房间 / 设备 / 指代前缀）
        if self._is_entity_reference(text):
            if not previous_user_message:
                # 语义路径依赖「上一轮意图」做参照；无上一轮时只能归还兜底层。
                # 保留语义引擎热身上下文层未来可注入「家庭实体池」后的扩展点。
                return ContextResolution(
                    matched=False,
                    needs_fallback=True,
                    explanation="指代但无上一轮上下文 → 兜底层",
                )
            prev_result = self._rule_engine.parse(previous_user_message)
            if not prev_result.matched:
                return ContextResolution(
                    matched=False,
                    needs_fallback=True,
                    explanation=f"上一轮意图不可继承: {prev_result.intent or 'unmatched'}",
                )
            inherited = self._inherit_from_previous(prev_result, text)
            if inherited is not None:
                return ContextResolution(
                    matched=True,
                    rule_result=inherited,
                    explanation="多轮指代：继承上一轮意图并替换实体",
                )
            # 启发式继承失败 → 退到语义召回：当前文本可能与上一轮是同义改写。
            semantic = self._try_semantic_recall(
                text, previous_user_message, prev_result
            )
            if semantic is not None:
                return ContextResolution(
                    matched=True,
                    rule_result=semantic,
                    explanation="语义召回：文本与上一轮高度相似，复用其意图",
                )
            return ContextResolution(
                matched=False,
                needs_fallback=True,
                explanation="无法从上一轮推导出目标实体 → 兜底层",
            )

        return ContextResolution(
            matched=False,
            needs_fallback=True,
            explanation="上下文层无法确定 → 兜底层",
        )

    # === 判定 ===

    @staticmethod
    def _is_relative_control(text: str) -> bool:
        return any(kw in text for kw in _RELATIVE_CONTROL)

    @staticmethod
    def _is_entity_reference(text: str) -> bool:
        """是否存在动作 verb？有 → 不认为是纯指代请求。"""
        if any(r.search(text) for r in _action_patterns()):
            return False
        # 指代前缀
        if any(p in text for p in _PRONOUN_PREFIXES):
            return True
        # 显式房间 / 设备列举
        if re.search(
            r"(客厅|卧室|主卧|次卧|厨房|餐厅|书房|卫浴|浴室|玄关|阳台|储物间|衣帽间|室内|房|厅)",
            text,
        ):
            return True
        return any(kw in text for kw in get_lexicon().device_hints)

    # === 继承推导 ===

    def _inherit_from_previous(
        self, prev: RuleParseResult, text: str
    ) -> RuleParseResult | None:
        """基于上一轮 ``prev`` 与当前 ``text`` 重建一个可执行结果。

        主要逻辑：把上一轮的 intent / action / entity 保留，替换
        ``entity_ref``（与可能的 entity 类型）为新提及的房间 / 设备。
        """
        new_ref, new_kind = self._extract_new_ref(text)
        if not new_ref:
            return None

        if prev.intent == "query":
            # 继承查询语义（温度 / 湿度 / 时钟），只替换目标房间
            return RuleParseResult(
                matched=True,
                intent="query",
                domain=prev.domain,
                confidence=_CONF_INHERIT,
                action=prev.action or "query_state",
                entity=prev.entity,
                entity_ref=new_ref,
                response_text="",
                elapsed_ms=0,
            )

        if prev.intent == "control" and prev.write_proposals:
            # 继承控制动作与参数；提案 args 不含 entity_ref（由执行器反查填充），
            # 因此可直接复用，仅替换 entity / entity_ref。
            return RuleParseResult(
                matched=True,
                intent="control",
                domain=prev.domain,
                confidence=_CONF_INHERIT,
                action=prev.action,
                entity=new_kind or prev.entity,
                entity_ref=new_ref,
                params=prev.params,
                write_proposals=prev.write_proposals,
                elapsed_ms=0,
            )

        if prev.intent == "scene" and prev.write_proposals:
            # 场景类通常不跨房间继承；仅当文本提到同一场景时才沿用（保守）。
            return None

        return None

    def _extract_new_ref(self, text: str) -> tuple[str, str]:
        """从当前文本抽取新的实体引用 ``(entity_ref, entity_kind)``。

        - 优先级：显式设备关键词 > 房间名 > 空。
        - ``entity_ref`` 保留用户在文本里的原始表述（如「厨房灯」「卧室」），
          由规则层执行器在家庭设备表中反查真实 device_id。
        """
        matched_kw = ""
        kind = ""
        for kw, kind_candidate in get_lexicon().device_hints.items():
            if kw in text:
                matched_kw = kw
                kind = kind_candidate
                break

        room = extract_room(text)
        if matched_kw:
            return f"{room}{matched_kw}" if room else matched_kw, kind
        if room:
            return room, ""
        return "", ""

    # === 语义召回 ===

    def _try_semantic_recall(
        self,
        text: str,
        previous_user_message: str,
        prev_result: RuleParseResult | None = None,
    ) -> RuleParseResult | None:
        """在启发式匹配失败后尝试用向量相似度做兜底消解。

        两种调用场景：

        1. **有上一轮**：当前文本与上一轮做相似度判断。超过阈值时，把
           上一轮的 ``RuleParseResult`` 原样返回（保持意图 / 动作 / 参数
           不变）；这种场景下即使 ``text`` 和 ``previous_user_message``
           字面完全不同，语义上也是同义改写。
        2. **无上一轮**：当前文本与该家庭「最近使用过的实体」做相似度。
           若任一实体相似度超过阈值，就当作显式指代返回 ``entity_ref``。
           这条路径当前没有上下文层可消费的实体池，保持返回 ``None``；
           设计上预留接口，调用方未来可注入 household context。

        任何异常 / 依赖不可用一律返回 ``None``，由调用方走兜底层。
        """
        if not self._embedder.available:
            return None
        if not text:
            return None
        threshold = get_settings().funnel_semantic_threshold
        # 「与上一轮相似」场景：复用 ``previous_user_message`` 的 parse 结果。
        if previous_user_message:
            return self._recall_against_previous(
                text, previous_user_message, threshold, prev_result
            )
        return self._recall_against_self(text, threshold)

    def _recall_against_previous(
        self,
        text: str,
        previous_user_message: str,
        threshold: float,
        prev_result: RuleParseResult | None = None,
    ) -> RuleParseResult | None:
        if prev_result is None:
            prev_result = self._rule_engine.parse(previous_user_message)
        if not prev_result.matched:
            return None
        vectors = self._embedder.encode([text, previous_user_message])
        if not vectors or len(vectors) < 2:
            return None
        sim = cosine_similarity(vectors[0], vectors[1])
        if sim < threshold:
            return None
        # 复用上一轮结果：意图 / 动作 / 参数 / 提案全部继承，仅 ``entity_ref``
        # 用新文本，让执行器重新反查。
        return RuleParseResult(
            matched=True,
            intent=prev_result.intent,
            domain=prev_result.domain,
            confidence=prev_result.confidence,
            action=prev_result.action,
            entity=prev_result.entity,
            entity_ref=text,
            params=prev_result.params,
            response_text=prev_result.response_text,
            write_proposals=prev_result.write_proposals,
            elapsed_ms=0,
        )

    def _recall_against_self(
        self,
        text: str,
        threshold: float,
    ) -> RuleParseResult | None:
        # 当前没有「家庭实体池」上下文；保留为未来扩展点。
        # 显式声明语义：调用方传 ``previous_user_message=""`` 不会得到独立召回。
        return None


# === 进程级单例 ===


_default_context_engine: ContextEngine | None = None


def get_context_engine() -> ContextEngine:
    """获取进程级单例 ``ContextEngine``。"""
    global _default_context_engine
    if _default_context_engine is None:
        _default_context_engine = ContextEngine()
    return _default_context_engine


def reset_context_engine() -> None:
    """重置单例（测试用）。"""
    global _default_context_engine
    _default_context_engine = None
