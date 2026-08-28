"""上下文层（Context Layer）多轮 / 指代消解引擎。

对应 ``docs/funnel-routing-architecture.md`` 第 6 节「第二层：上下文层（专科医生）」
与第 11 节「P1：上下文层多轮与指代」。

职责
----

当漏斗路由器把请求判为 ``LAYER_CONTEXT``（规则层模糊命中、含指代词 / 相对控制、
存在活动对话）时，本引擎在**不调用任何 LLM** 的前提下做确定性多轮 / 指代消解，
让「话只说一半」的请求在进入大模型前被接住：

- **意图继承 + 实体替换（Anaphora）**：如上一轮问「客厅温度多少」，本轮说
  「那卧室呢？」→ 继承 ``query_temp`` 意图，把实体替换为 ``bedroom``。
- **实体复用（Ellipsis）**：如上一轮「打开客厅灯」，本轮「厨房灯」→ 继承
  ``control`` 意图与动作，把目标实体替换为 ``kitchen_light``。
- **无法确定（Relative / Compound / Unclear）**：仍归还给上层（兜底层），由
  LLM 处理。典型如「声音大一点」（需要设备实时状态）、「那它呢」（无实体）。

设计说明
--------

- **确定性优先**：本层是规则层的延伸，只处理「能根据上一轮明确推导」的场景；
  一旦无法唯一确定，立即 ``needs_fallback=True``，绝不让多轮对话失控。
- **0 Token**：本层不调用模型，只读会话树历史做轻量解析。
- **与写路径一致**：推导出的可执行结果仍以 ``RuleParseResult`` 暴露，交由
  ``execute_rule_layer`` 执行，写操作继续走 ``risk_check → approval`` 单写路径，
  不因「更省」而绕过风险控制。

不覆盖的场景
------------

- 需要设备实时状态的相对控制（音量 / 色温 ±step）→ 由兜底层结合状态工具处理。
- 复杂多轮槽位填充（「帮我定个闹钟」「明早七点」）→ 由兜底层 / 后续小模型处理。
- 跨域复合意图 → 由兜底层处理。

该实现遵循文档第 10 节「渐进式演进：初期可把上下文层硬编码为规则；数据积累后再
训练小模型」。Slot 状态机与家庭图谱 System Prompt 注入属后续演进，本期通过
``SessionState`` / ``previous_user_message`` 传递必要的多轮信号。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.agents.subagents.rule_engine import (
    _ROOM_DEVICE_HINTS,
    _SET_POS_RE,
    _SET_TEMP_RE,
    _TURN_OFF_RE,
    _TURN_ON_RE,
    _QUERY_RE,
    RuleEngine,
    RuleParseResult,
    get_rule_engine,
)

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
_HAS_ACTION = (_TURN_ON_RE, _TURN_OFF_RE, _SET_TEMP_RE, _SET_POS_RE, _QUERY_RE)
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

    def __init__(self, *, rule_engine: RuleEngine | None = None):
        self._rule_engine = rule_engine or get_rule_engine()

    # ------------------------------------------------------------------
    # 公开 API
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # 内部实现
    # ------------------------------------------------------------------

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
            if inherited is None:
                return ContextResolution(
                    matched=False,
                    needs_fallback=True,
                    explanation="无法从上一轮推导出目标实体 → 兜底层",
                )
            return ContextResolution(
                matched=True,
                rule_result=inherited,
                explanation="多轮指代：继承上一轮意图并替换实体",
            )

        return ContextResolution(
            matched=False,
            needs_fallback=True,
            explanation="上下文层无法确定 → 兜底层",
        )

    # ------------------------------------------------------------------
    # 判定
    # ------------------------------------------------------------------

    @staticmethod
    def _is_relative_control(text: str) -> bool:
        return any(kw in text for kw in _RELATIVE_CONTROL)

    @staticmethod
    def _is_entity_reference(text: str) -> bool:
        """是否存在动作 verb？有 → 不认为是纯指代请求。"""
        if any(r.search(text) for r in _HAS_ACTION):
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
        return any(kw in text for kw in _ROOM_DEVICE_HINTS)

    # ------------------------------------------------------------------
    # 继承推导
    # ------------------------------------------------------------------

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
        for kw, kind_candidate in _ROOM_DEVICE_HINTS.items():
            if kw in text:
                matched_kw = kw
                kind = kind_candidate
                break

        room = self._rule_engine._extract_room(text)  # noqa: SLF001 复用规则层房间抽取
        if matched_kw:
            return f"{room}{matched_kw}" if room else matched_kw, kind
        if room:
            return room, ""
        return "", ""


# ---------------------------------------------------------------------------
# 进程级单例
# ---------------------------------------------------------------------------


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
