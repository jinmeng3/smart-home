"""简单查询解析器：「现在几点了」「客厅温度多少」「湿度呢」。

本层不查任何数据——只识别"要查什么"，实际取值由 ``rule_layer`` 的
``_answer_simple_query`` 完成，因此 ``response_text`` 留空。
"""

from __future__ import annotations

from app.agents.subagents.lexicon import (
    QUERY_CLOCK_RE,
    QUERY_HUMIDITY_RE,
    QUERY_TEMPERATURE_RE,
)
from app.agents.subagents.parsers.base import RuleContext, RuleParseResult
from app.agents.subagents.parsers.extract import extract_room


class QueryParser:
    """状态查询（最廉价，优先级最高）。"""

    name = "query"
    priority = 10

    def try_parse(self, ctx: RuleContext) -> RuleParseResult | None:
        text = ctx.text
        # 没有查询信号词直接退出，避免后续三个正则的开销
        if not ctx.lexicon.query_state_re.search(text):
            return None

        if QUERY_CLOCK_RE.search(text):
            return RuleParseResult(
                matched=True,
                intent="query",
                domain="device",
                confidence=ctx.conf_high,
                action="query_state",
                entity="clock",
                response_text="",  # 由 rule_layer 填入当前时间
                elapsed_ms=ctx.elapsed_ms(),
            )

        if QUERY_TEMPERATURE_RE.search(text):
            return RuleParseResult(
                matched=True,
                intent="query",
                domain="comfort",
                confidence=ctx.conf_high,
                action="query_state",
                entity="temperature",
                entity_ref=extract_room(text),
                response_text="",
                elapsed_ms=ctx.elapsed_ms(),
            )

        if QUERY_HUMIDITY_RE.search(text):
            return RuleParseResult(
                matched=True,
                intent="query",
                domain="comfort",
                confidence=ctx.conf_high,
                action="query_state",
                entity="humidity",
                entity_ref=extract_room(text),
                response_text="",
                elapsed_ms=ctx.elapsed_ms(),
            )

        return None
