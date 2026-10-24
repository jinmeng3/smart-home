"""规则层回归测试：覆盖四类 parser、拒识路径、词表合并与别名反查。

这批断言对应重构前 ``RuleEngine`` 的既有行为，用于确认
"抽 AliasIndex / 词表外置 / 拆 parsers" 三步重构没有改变解析结果。

运行：``uv run pytest tests/test_rule_engine.py -v``
"""

from __future__ import annotations

from typing import ClassVar, cast

import pytest

from app.agents.subagents.alias_index import AliasIndex
from app.agents.subagents.lexicon import (
    DEFAULT_DEVICE_HINTS,
    DEFAULT_SCENE_KEYWORDS,
    DEFAULT_TURN_ON_PATTERNS,
    RuleLexicon,
    build_lexicon,
)
from app.agents.subagents.parsers import default_parsers
from app.agents.subagents.parsers.extract import (
    detect_action,
    extract_room,
    find_mention,
    parse_chinese_number,
)
from app.agents.subagents.rule_engine import RuleEngine


@pytest.fixture
def engine() -> RuleEngine:
    return RuleEngine()


# === 查询 ===


@pytest.mark.parametrize(
    ("message", "entity"),
    [
        ("现在几点了", "clock"),
        ("现在时间", "clock"),
        ("客厅温度多少", "temperature"),
        ("卧室湿度多少", "humidity"),
    ],
)
def test_query_parser(engine: RuleEngine, message: str, entity: str) -> None:
    result = engine.parse(message)
    assert result.matched
    assert result.intent == "query"
    assert result.entity == entity
    assert result.action == "query_state"
    # 查询类不产生写提案
    assert result.write_proposals == ()


def test_query_extracts_room(engine: RuleEngine) -> None:
    result = engine.parse("卧室温度多少")
    assert result.entity_ref == "卧室"


# === 场景 ===


@pytest.mark.parametrize(
    ("message", "scene_id"),
    [
        ("我回来了", "home"),
        ("离家", "leave"),
        ("晚安", "sleep"),
        ("早安", "wake"),
        ("观影模式", "movie"),
    ],
)
def test_scene_parser(engine: RuleEngine, message: str, scene_id: str) -> None:
    result = engine.parse(message)
    assert result.matched
    assert result.intent == "scene"
    assert result.entity_ref == scene_id
    assert len(result.write_proposals) == 1
    proposal = result.write_proposals[0]
    assert proposal.tool == "execute_scene"
    # args 留空：真实 scene_id 由 rule_layer._resolve_scene 按家庭反查后注入
    # （与设备提案不带 device_id 是同一套约定，见 scene.py 顶部注释）。
    # 场景意图标识走 params["scene_key"]。
    assert proposal.args == {}
    assert result.params.get("scene_key") == scene_id


# === 控制 ===


def test_control_turn_on(engine: RuleEngine) -> None:
    result = engine.parse("打开客厅灯")
    assert result.matched
    assert result.intent == "control"
    assert result.action == "on"
    assert result.entity == "light"
    assert "灯" in result.entity_ref
    assert result.write_proposals[0].tool == "set_device_power"
    assert result.write_proposals[0].args == {"power": "on"}


def test_control_turn_off(engine: RuleEngine) -> None:
    result = engine.parse("关闭卧室灯")
    assert result.matched
    assert result.action == "off"
    assert result.write_proposals[0].args == {"power": "off"}


def test_control_set_temperature(engine: RuleEngine) -> None:
    result = engine.parse("空调调到26度")
    assert result.matched
    assert result.action == "set_temperature"
    assert result.entity == "air_conditioner"
    assert result.params["temperature"] == pytest.approx(26.0)
    assert result.write_proposals[0].tool == "set_device_temperature"


def test_control_set_position(engine: RuleEngine) -> None:
    result = engine.parse("窗帘开到50%")
    assert result.matched
    assert result.action == "set_position"
    assert result.entity == "curtain"
    assert result.write_proposals[0].tool == "set_curtain_position"
    assert result.write_proposals[0].args == {"position": 50}


def test_control_rejects_bare_verb(engine: RuleEngine) -> None:
    """只说「打开」没有实体 → 必须拒识，避免误触执行。"""
    result = engine.parse("打开")
    assert not result.matched
    assert result.write_proposals == ()


def test_control_write_proposal_has_no_device_id(engine: RuleEngine) -> None:
    """规则层不查设备表，提案里不得出现 device_id。"""
    result = engine.parse("打开客厅灯")
    for proposal in result.write_proposals:
        assert "device_id" not in proposal.args


# === 快捷自动化 ===


def test_schedule_arabic_number(engine: RuleEngine) -> None:
    result = engine.parse("10分钟后关电视")
    assert result.matched
    assert result.intent == "schedule"
    assert result.params["delay_seconds"] == 600
    assert result.needs_clarification
    assert result.write_proposals[0].args["delay_seconds"] == 600


def test_schedule_chinese_number(engine: RuleEngine) -> None:
    result = engine.parse("十分钟后关电视")
    assert result.matched
    assert result.intent == "schedule"
    assert result.params["delay_seconds"] == 600


def test_schedule_beats_control(engine: RuleEngine) -> None:
    """含延时的指令必须落到 schedule，不能被 control 当成立即执行。"""
    result = engine.parse("30秒后打开客厅灯")
    assert result.intent == "schedule"
    assert result.params["delay_seconds"] == 30


# === 复合意图拒识 ===


@pytest.mark.parametrize(
    "message",
    [
        "我睡觉了，顺便看看明天天气",
        "打开灯还有关窗帘",
        "决定要不要开加湿器",
        "帮我开灯，然后关电视",
    ],
)
def test_composite_intent_rejected(engine: RuleEngine, message: str) -> None:
    result = engine.parse(message)
    assert not result.matched
    assert result.intent == "composite"


def test_empty_message_rejected(engine: RuleEngine) -> None:
    for message in ("", "   "):
        result = engine.parse(message)
        assert not result.matched
    # None 也要能兜住（历史调用方可能传 None）
    assert not engine.parse(cast(str, None)).matched


def test_unknown_message_rejected(engine: RuleEngine) -> None:
    result = engine.parse("帮我算一下房贷利率")
    assert not result.matched
    assert result.intent == ""


# === 别名反查 ===


def test_alias_index_resolves_device() -> None:
    index = AliasIndex(household_id=1)
    index.set_device_aliases({"客厅主灯": ["客厅大灯", "大灯"]})
    assert index.resolve_device("大灯") == "客厅主灯"
    assert index.resolve_device("客厅大灯") == "客厅主灯"
    assert index.resolve_device("不存在的灯") == ""


def test_alias_index_conflict_returns_empty() -> None:
    index = AliasIndex(household_id=1)
    index.set_room_aliases({"客厅": ["大厅"]})
    index.set_room_aliases({"餐厅": ["大厅"]})
    assert index.has_conflict("大厅")
    assert index.resolve_room("大厅") == ""


def test_alias_index_version_bumps_only_on_change() -> None:
    index = AliasIndex(household_id=1)
    assert index.version == 0
    index.set_device_aliases({"客厅主灯": ["大灯"]})
    first = index.version
    assert first > 0
    # 写入完全相同的映射不应触发热加载
    index.set_device_aliases({"客厅主灯": ["大灯"]})
    assert index.version == first


def test_engine_uses_alias_index() -> None:
    index = AliasIndex(household_id=1)
    index.set_device_aliases({"客厅主灯": ["客厅灯"]})
    engine = RuleEngine(alias_index=index)
    result = engine.parse("打开客厅灯")
    assert result.matched
    assert result.entity_ref == "客厅主灯"


# === 词表 ===


def test_lexicon_defaults_intact() -> None:
    lexicon = RuleLexicon()
    assert lexicon.device_hints == DEFAULT_DEVICE_HINTS
    assert lexicon.turn_on_patterns == DEFAULT_TURN_ON_PATTERNS
    assert lexicon.scene_keywords == DEFAULT_SCENE_KEYWORDS


def test_lexicon_merge_appends_device_hint() -> None:
    class FakeSettings:
        rule_lexicon_extra_device_hints: ClassVar[dict[str, str]] = {"地灯": "light"}
        rule_lexicon_extra_turn_on = None
        rule_lexicon_extra_turn_off = None
        rule_lexicon_extra_query_state = None
        rule_lexicon_extra_scene_keywords = None

    lexicon = build_lexicon(FakeSettings())
    assert lexicon.device_hints["地灯"] == "light"
    # 默认词条仍在，且顺序在前（优先级更高）
    assert lexicon.device_hints["灯"] == "light"
    assert next(iter(lexicon.device_hints)) == "灯"


def test_lexicon_merge_appends_scene_phrase() -> None:
    class FakeSettings:
        rule_lexicon_extra_device_hints = None
        rule_lexicon_extra_turn_on = None
        rule_lexicon_extra_turn_off = None
        rule_lexicon_extra_query_state = None
        rule_lexicon_extra_scene_keywords: ClassVar[dict[str, list[str]]] = {
            "home": ["我到了"],
            "party": ["开派对"],
        }

    lexicon = build_lexicon(FakeSettings())
    assert "我到了" in lexicon.scene_keywords["home"]
    # 原有短语保留
    assert "回家" in lexicon.scene_keywords["home"]
    # 新场景 ID 加入
    assert lexicon.scene_keywords["party"] == ("开派对",)


def test_lexicon_merge_dedupes_patterns() -> None:
    class FakeSettings:
        rule_lexicon_extra_device_hints = None
        # "打开" 已在默认词表里，不应重复追加
        rule_lexicon_extra_turn_on: ClassVar[list[str]] = ["打开", "给我开"]
        rule_lexicon_extra_turn_off = None
        rule_lexicon_extra_query_state = None
        rule_lexicon_extra_scene_keywords = None

    lexicon = build_lexicon(FakeSettings())
    assert lexicon.turn_on_patterns.count("打开") == 1
    assert "给我开" in lexicon.turn_on_patterns


def test_custom_lexicon_takes_effect() -> None:
    lexicon = RuleLexicon(scene_keywords={"party": ("开派对",)})
    engine = RuleEngine(lexicon=lexicon)
    result = engine.parse("开派对")
    assert result.matched
    assert result.entity_ref == "party"
    # 自定义词表里没有 home，原短语不应命中场景
    assert engine.parse("我回来了").intent != "scene"


# === 抽取函数 ===


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("客厅温度", "客厅"),
        ("宝宝房的灯", "宝宝"),
        ("主卧空调", "主卧"),
        ("帮我算房贷", "帮我算"),  # 「X房」规则的已知副作用
        ("没有房间", ""),
    ],
)
def test_extract_room(text: str, expected: str) -> None:
    assert extract_room(text) == expected


def test_detect_action_prefers_setter_over_bare_verb() -> None:
    lexicon = RuleLexicon()
    # "空调调到26度" 同时含「调到」和「开」的可能，必须判定为 set_temperature
    assert detect_action("空调调到26度", lexicon) == "set_temperature"
    assert detect_action("打开灯", lexicon) == "on"
    assert detect_action("关灯", lexicon) == "off"
    assert detect_action("你好", lexicon) is None


def test_find_mention_keeps_user_wording() -> None:
    assert find_mention("把客厅大灯打开", "灯", "客厅", RuleLexicon()) == "客厅大灯"


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("十", 10),
        ("十二", 12),
        ("一百二十三", 123),
        ("30", 30),
        ("", 1),
        ("不是数字", 1),
    ],
)
def test_parse_chinese_number(text: str, expected: int) -> None:
    assert parse_chinese_number(text) == expected


# === 解析器注册 ===


def test_default_parsers_priority_order() -> None:
    parsers = default_parsers()
    priorities = [p.priority for p in parsers]
    assert priorities == sorted(priorities)
    names = [p.name for p in parsers]
    # schedule 必须早于 control
    assert names.index("schedule") < names.index("control")


def test_custom_parser_can_be_injected() -> None:
    class AlwaysMatchParser:
        name = "always"
        priority = 1

        def try_parse(self, ctx):
            from app.agents.subagents.parsers.base import RuleParseResult

            return RuleParseResult(
                matched=True, intent="custom", elapsed_ms=ctx.elapsed_ms()
            )

    engine = RuleEngine(parsers=[AlwaysMatchParser()])
    result = engine.parse("随便说点什么")
    assert result.matched
    assert result.intent == "custom"


def test_parser_exception_is_swallowed() -> None:
    class BoomParser:
        name = "boom"
        priority = 1

        def try_parse(self, ctx):
            raise RuntimeError("boom")

    engine = RuleEngine(parsers=[BoomParser()])
    result = engine.parse("打开客厅灯")
    # 解析器异常不外泄，降级为拒识
    assert not result.matched


def test_elapsed_ms_recorded() -> None:
    engine = RuleEngine()
    result = engine.parse("打开客厅灯")
    assert result.elapsed_ms >= 0
