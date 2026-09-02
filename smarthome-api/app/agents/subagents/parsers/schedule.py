"""快捷自动化解析器：「十分钟后关电视」「等 30 秒开灯」。

本层**不直接执行**（定时器依赖边缘网关），而是把写提案 + ``delay_seconds``
透传给上层；上层可选择写入本地定时器或交给 LLM 走 ``create_automation``。

依赖注入：延时表达只决定"什么时候做"，"做什么"复用 :class:`ControlParser`。
"""

from __future__ import annotations

from app.agents.subagents.lexicon import DELAY_UNIT_SECONDS, SCHEDULE_DELAY_RE
from app.agents.subagents.parsers.base import (
    RuleContext,
    RuleParseResult,
    WriteProposal,
)
from app.agents.subagents.parsers.control import ControlParser
from app.agents.subagents.parsers.extract import parse_chinese_number

# 无法识别单位时的兜底倍率（按分钟算，比按秒算更符合家庭场景直觉）。
_FALLBACK_MULTIPLIER = 60


class ScheduleParser:
    """带延时的快捷自动化。

    优先级高于 :class:`ControlParser`——「十分钟后关电视」必须先被识别为
    schedule，否则会被 control 当成"立即关电视"执行。
    """

    name = "schedule"
    priority = 30

    def __init__(self, control_parser: ControlParser | None = None) -> None:
        # 复用 control 解析"做什么"；允许注入以便测试
        self._control = control_parser or ControlParser()

    def try_parse(self, ctx: RuleContext) -> RuleParseResult | None:
        delay_match = SCHEDULE_DELAY_RE.search(ctx.text)
        if delay_match is None:
            return None

        # 两组备选：「10分钟后」走 group(1,2)，「等10分钟」走 group(3,4)
        raw_amount = delay_match.group(1) or delay_match.group(3)
        unit = delay_match.group(2) or delay_match.group(4)
        amount = parse_chinese_number(raw_amount)
        multiplier = DELAY_UNIT_SECONDS.get(unit, _FALLBACK_MULTIPLIER)
        delay_seconds = amount * multiplier

        base = self._control.try_parse(ctx)
        if base is None or not base.write_proposals:
            return None

        enriched_params = dict(base.params)
        enriched_params["delay_seconds"] = delay_seconds
        new_proposals = tuple(
            WriteProposal(
                tool=proposal.tool,
                args={**proposal.args, "delay_seconds": delay_seconds},
            )
            for proposal in base.write_proposals
        )

        return RuleParseResult(
            matched=True,
            intent="schedule",
            domain=base.domain,
            confidence=ctx.conf_mid,
            action=base.action,
            entity=base.entity,
            entity_ref=base.entity_ref,
            params=enriched_params,
            write_proposals=new_proposals,
            # 延时操作是"未来动作"，一律追问确认
            needs_clarification=True,
            clarification_prompt=(
                f"将在 {amount}{unit}后执行该操作，届时是否需要二次确认？"
            ),
            elapsed_ms=ctx.elapsed_ms(),
        )
