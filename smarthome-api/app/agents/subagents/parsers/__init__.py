"""规则层子解析器集合。

新增一类意图 = 新增一个实现 :class:`RuleParser` 的类 + 注册进
:func:`default_parsers`（或由调用方在构造 ``RuleEngine`` 时传入自定义列表），
**不需要改动 ``rule_engine.py``**。

优先级约定（``priority`` 小者先执行，10 的倍数便于插入）：

===========  ==========  ====================================================
priority     parser      说明
===========  ==========  ====================================================
10           query       最廉价，纯正则
20           scene       固定短语子串扫描
30           schedule    含延时；**必须早于 control**，否则「十分钟后关灯」
                         会被当成「立即关灯」
40           control     最贵（动作识别 + 实体抽取 + 别名反查）
===========  ==========  ====================================================
"""

from __future__ import annotations

from app.agents.subagents.parsers.base import (
    RuleContext,
    RuleParser,
    RuleParseResult,
    WriteProposal,
)
from app.agents.subagents.parsers.control import ControlParser
from app.agents.subagents.parsers.query import QueryParser
from app.agents.subagents.parsers.scene import SceneParser
from app.agents.subagents.parsers.schedule import ScheduleParser


def default_parsers() -> list[RuleParser]:
    """内置解析器列表（已按 ``priority`` 排序）。

    ``ScheduleParser`` 复用同一个 ``ControlParser`` 实例，避免重复构造。
    """
    control = ControlParser()
    return [
        QueryParser(),
        SceneParser(),
        ScheduleParser(control_parser=control),
        control,
    ]


__all__ = [
    "ControlParser",
    "QueryParser",
    "RuleContext",
    "RuleParseResult",
    "RuleParser",
    "SceneParser",
    "ScheduleParser",
    "WriteProposal",
    "default_parsers",
]
