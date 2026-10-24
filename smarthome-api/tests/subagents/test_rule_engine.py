"""规则层（Rule Engine）单元测试。"""

import pytest

from app.agents.subagents.rule_engine import (
    AliasIndex,
    RuleEngine,
    get_rule_engine,
)

# ---------------------------------------------------------------------------
# 直接控制
# ---------------------------------------------------------------------------


class TestControlIntent:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_open_light_in_living_room(self):
        result = self.engine.parse("打开客厅灯")
        assert result.matched
        assert result.intent == "control"
        assert result.action == "on"
        assert result.entity == "light"
        assert result.entity_ref == "客厅灯"
        assert result.confidence >= 0.95
        assert len(result.write_proposals) == 1
        proposal = result.write_proposals[0]
        assert proposal.tool == "set_device_power"
        assert proposal.args == {"power": "on"}

    def test_close_curtain(self):
        result = self.engine.parse("关闭窗帘")
        assert result.matched
        assert result.action == "off"
        assert result.entity == "curtain"
        assert result.entity_ref == "窗帘"
        assert result.confidence >= 0.95

    def test_set_temperature(self):
        result = self.engine.parse("空调调到 26 度")
        assert result.matched
        assert result.action == "set_temperature"
        assert result.entity == "air_conditioner"
        assert result.params.get("temperature") == pytest.approx(26.0)
        assert result.write_proposals[0].tool == "set_device_temperature"
        assert result.write_proposals[0].args["temperature"] == pytest.approx(26.0)

    def test_set_curtain_position(self):
        result = self.engine.parse("窗帘开到 50%")
        assert result.matched
        assert result.action == "set_position"
        assert result.entity == "curtain"
        assert result.params.get("position") == 50
        assert result.write_proposals[0].tool == "set_curtain_position"
        assert result.write_proposals[0].args["position"] == 50

    def test_various_open_verbs(self):
        for phrase in ["开灯", "帮我开客厅灯", "启动空调", "亮一下客厅的灯"]:
            result = self.engine.parse(phrase)
            assert result.matched, f"未匹配: {phrase}"
            assert result.action == "on", f"动作错误: {phrase}"

    def test_various_close_verbs(self):
        for phrase in ["关灯", "帮我关灯", "关闭客厅灯", "关上窗帘"]:
            result = self.engine.parse(phrase)
            assert result.matched, f"未匹配: {phrase}"
            assert result.action == "off", f"动作错误: {phrase}"


# ---------------------------------------------------------------------------
# 固定场景
# ---------------------------------------------------------------------------


class TestSceneIntent:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_home_scene(self):
        result = self.engine.parse("我回来了")
        assert result.matched
        assert result.intent == "scene"
        assert result.entity_ref == "home"
        assert result.write_proposals[0].tool == "execute_scene"
        # args 留空：真实 scene_id 由 rule_layer._resolve_scene 按家庭反查后注入
        # （场景意图标识走 params["scene_key"]，与顶层 test_rule_engine.py 一致）。
        assert result.write_proposals[0].args == {}
        assert result.params.get("scene_key") == "home"
        assert result.confidence >= 0.95

    def test_sleep_scene(self):
        result = self.engine.parse("晚安")
        assert result.matched
        assert result.entity_ref == "sleep"

    def test_leave_scene(self):
        result = self.engine.parse("我出门了")
        assert result.matched
        assert result.entity_ref == "leave"

    def test_movie_scene(self):
        result = self.engine.parse("观影模式")
        assert result.matched
        assert result.entity_ref == "movie"


# ---------------------------------------------------------------------------
# 简单查询
# ---------------------------------------------------------------------------


class TestQueryIntent:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_query_clock(self):
        result = self.engine.parse("现在几点了")
        assert result.matched
        assert result.intent == "query"
        assert result.entity == "clock"
        assert result.confidence >= 0.95

    def test_query_temperature(self):
        result = self.engine.parse("室内温度多少")
        assert result.matched
        assert result.intent == "query"
        assert result.entity == "temperature"
        assert result.entity_ref == "室内"

    def test_query_humidity(self):
        result = self.engine.parse("湿度怎么样")
        assert result.matched
        assert result.entity == "humidity"


# ---------------------------------------------------------------------------
# 快捷自动化（带时间）
# ---------------------------------------------------------------------------


class TestScheduleIntent:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_schedule_close_tv_in_10_min(self):
        result = self.engine.parse("十分钟后关电视")
        assert result.matched
        assert result.intent == "schedule"
        assert result.params.get("delay_seconds") == 600
        assert result.write_proposals[0].args["delay_seconds"] == 600
        # 0.85 置信度需要追问
        assert result.needs_clarification

    def test_no_delay_no_match(self):
        result = self.engine.parse("打开客厅灯")
        assert result.intent != "schedule"


# ---------------------------------------------------------------------------
# 拒识 / 性能
# ---------------------------------------------------------------------------


class TestRejection:
    def setup_method(self):
        self.engine = RuleEngine()

    def test_empty_message(self):
        result = self.engine.parse("")
        assert not result.matched

    def test_open_without_target(self):
        # 仅有动作，没有设备 → 拒识
        result = self.engine.parse("打开")
        assert not result.matched

    def test_complex_intent_falls_through(self):
        # 包含指代词 / 多轮 / 复合 → 拒识（应由上下文层 / 兜底层处理）
        result = self.engine.parse("那卧室呢？")
        assert not result.matched

    def test_long_phrase_does_not_hang(self):
        # 性能预算 < 50ms
        result = self.engine.parse("打开" * 100 + "客厅灯")
        assert result.matched
        assert result.elapsed_ms < 50


# ---------------------------------------------------------------------------
# 别名倒排索引
# ---------------------------------------------------------------------------


class TestAliasIndex:
    def test_resolve_room(self):
        index = AliasIndex(household_id=1)
        index.set_room_aliases({"宝宝房": ["宝宝房", "BB房", "小卧室"]})
        assert index.resolve_room("宝宝房") == "宝宝房"
        assert index.resolve_room("BB房") == "宝宝房"
        assert index.resolve_room("不存在的房间") == ""

    def test_resolve_device(self):
        index = AliasIndex(household_id=1)
        index.set_device_aliases({"客厅吊灯": ["客厅吊灯", "大灯"]})
        assert index.resolve_device("大灯") == "客厅吊灯"
        assert index.resolve_device("客厅吊灯") == "客厅吊灯"

    def test_conflict_marks_index(self):
        index = AliasIndex(household_id=1)
        index.set_room_aliases({"主卧": ["主卧"]})
        index.set_room_aliases({"主卧室": ["主卧"]})  # 同一别名映射到不同 canonical
        assert index.has_conflict("主卧")
        assert index.resolve_room("主卧") == ""

    def test_isolated_per_household(self):
        # 不同家庭的别名不应互相影响（虽然当前 API 暴露 family，但构造已绑定）
        a = AliasIndex(household_id=1)
        b = AliasIndex(household_id=2)
        a.set_room_aliases({"主卧": ["主卧"]})
        assert a.resolve_room("主卧") == "主卧"
        assert b.resolve_room("主卧") == ""


# ---------------------------------------------------------------------------
# 别名 + 解析器集成
# ---------------------------------------------------------------------------


class TestAliasIntegration:
    def test_uses_alias_to_resolve(self):
        index = AliasIndex(household_id=1)
        index.set_device_aliases({"客厅灯": ["大灯"]})
        engine = RuleEngine(alias_index=index)
        result = engine.parse("打开大灯")
        assert result.matched
        assert result.entity_ref == "客厅灯"


# ---------------------------------------------------------------------------
# 单例
# ---------------------------------------------------------------------------


def test_get_rule_engine_returns_singleton():
    a = get_rule_engine()
    b = get_rule_engine()
    assert a is b
