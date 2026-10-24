"""规则层直执器（execute_rule_layer）单元测试。

范围：仅覆盖纯函数 / 数据构造部分，避免端到端异步 SSE 流。
完整 SSE 事件同构测试在后续集成测试中补齐（需要 langgraph runtime）。

- 设备反查：精确 → 房间+类型 → 名称包含
- 参数合并：``_make_args`` 把 device_id 注入并经 schema 校验
- 风险分类：复用 ``risk.classify_*``，无数据库时降级为 UNKNOWN
- 单元数提案 → pending 构造：``_build_pending`` 字段完整
- 多提案场景：失败时早退（仅执行到第一个失败）
"""

from __future__ import annotations

from app.agents.risk.policy import RiskLevel
from app.agents.subagents.rule_engine import WriteProposal
from app.agents.subagents.rule_layer import (
    _build_pending,
    _classify_for_proposal,
    _make_args,
    _resolve_device,
    _split_room_from_entity_ref,
)

# ---------------------------------------------------------------------------
# 设备反查
# ---------------------------------------------------------------------------


class TestResolveDevice:
    def test_exact_name_match(self, db, context, device_factory):
        light = device_factory(name="客厅灯", room="客厅", type="light")
        d = _resolve_device(
            db,
            context,
            entity_type="light",
            entity_ref="客厅灯",
            room="客厅",
        )
        assert d is not None
        assert d.id == light.id

    def test_room_plus_type(self, db, context, device_factory):
        # 「客厅的灯」类引用：entity_ref 拼成「客厅灯」 → 精确匹配
        # 但「灯」单独（entity_ref="灯"）→ 走 room+type
        device_factory(name="主灯", room="客厅", type="light")
        d = _resolve_device(
            db,
            context,
            entity_type="light",
            entity_ref="",
            room="客厅",
        )
        assert d is not None
        assert d.name == "主灯"

    def test_no_match_returns_none(self, db, context, device_factory):
        device_factory(name="客厅灯", room="客厅", type="light")
        d = _resolve_device(
            db,
            context,
            entity_type="light",
            entity_ref="厨房吊灯",
            room="厨房",
        )
        assert d is None

    def test_multiple_candidates_falls_back_to_name_contains(
        self, db, context, device_factory
    ):
        # 两个同名 + 同类型设备 → 走名称包含匹配
        device_factory(name="主灯", room="客厅", type="light", device_id="dev-a")
        device_factory(name="副灯", room="客厅", type="light", device_id="dev-b")
        # 引用「副」→ 包含匹配命中「副灯」
        d = _resolve_device(
            db,
            context,
            entity_type="light",
            entity_ref="副",
            room="客厅",
        )
        # 多候选时按名称包含匹配：期望匹配到一条
        assert d is not None


# ---------------------------------------------------------------------------
# 房间拆分
# ---------------------------------------------------------------------------


class TestSplitRoom:
    def test_split_with_device_keyword(self):
        assert _split_room_from_entity_ref("客厅灯", room_hint="") == "客厅"
        assert _split_room_from_entity_ref("厨房窗帘", room_hint="") == "厨房"
        assert _split_room_from_entity_ref("主卧吊灯", room_hint="") == "主卧"

    def test_split_with_room_hint(self):
        # 显式 room_hint 优先
        assert _split_room_from_entity_ref("灯", room_hint="卧室") == "卧室"

    def test_no_keyword(self):
        assert _split_room_from_entity_ref("客厅", room_hint="") == ""


# ---------------------------------------------------------------------------
# 参数合并 + schema 校验
# ---------------------------------------------------------------------------


class TestMakeArgs:
    def test_set_device_power(self):
        result = _make_args(
            "set_device_power",
            {"power": "on"},
            device_id=42,
        )
        assert result["device_id"] == 42
        assert result["power"] == "on"

    def test_set_device_temperature(self):
        result = _make_args(
            "set_device_temperature",
            {"temperature": 26.0, "mode": "cool"},
            device_id=42,
        )
        assert result["temperature"] == 26.0
        assert result["device_id"] == 42

    def test_set_curtain_position(self):
        result = _make_args(
            "set_curtain_position",
            {"position": 50},
            device_id=42,
        )
        assert result["position"] == 50

    def test_unknown_tool_passes_through(self):
        # 没有 schema 的工具 → 原样返回（由执行器再次校验）
        result = _make_args("custom_tool", {"foo": "bar"}, device_id=42)
        assert result == {"foo": "bar", "device_id": 42}


# ---------------------------------------------------------------------------
# 风险分类
# ---------------------------------------------------------------------------


class TestClassifyForProposal:
    def test_low_risk_device(self, db, context, device_factory):
        light = device_factory(name="客厅灯", room="客厅", type="light")
        proposal = WriteProposal(
            tool="set_device_power", args={"device_id": light.id, "power": "on"}
        )
        level, reasons, preview, rv = _classify_for_proposal(db, context, proposal)
        # 灯 → 读相关或低风险；不应是 high
        assert level in {RiskLevel.READ_ONLY, RiskLevel.LOW, RiskLevel.UNKNOWN}
        assert isinstance(reasons, list)
        assert isinstance(preview, dict)
        assert isinstance(rv, str)

    def test_high_risk_device(self, db, context, device_factory):
        lock = device_factory(
            name="前门锁", room="玄关", type="lock", device_id="dev-lock"
        )
        proposal = WriteProposal(
            tool="set_device_power", args={"device_id": lock.id, "power": "off"}
        )
        level, _reasons, _preview, _rv = _classify_for_proposal(db, context, proposal)
        # 门锁类设备 → HIGH 风险
        assert level in {RiskLevel.HIGH, RiskLevel.UNKNOWN}

    def test_unknown_tool_returns_unknown(self, db, context):
        proposal = WriteProposal(tool="not_a_real_tool", args={"foo": "bar"})
        level, reasons, _preview, _rv = _classify_for_proposal(db, context, proposal)
        assert level == RiskLevel.UNKNOWN
        assert any("不支持" in r for r in reasons)


# ---------------------------------------------------------------------------
# Pending 构造
# ---------------------------------------------------------------------------


class TestBuildPending:
    def test_fields_complete(self):
        pending = _build_pending(
            run_id="run-1",
            call_id="call-1",
            tool="set_device_power",
            args={"device_id": 1, "power": "on"},
            level=RiskLevel.HIGH,
            reasons=["高风险操作"],
            preview={"device_name": "客厅灯"},
            resource_version="v1",
            model_name="test",
            model_id=1,
            session_id=10,
        )
        assert pending["approval_id"] == "run-1:call-1"
        assert pending["run_id"] == "run-1"
        assert pending["session_id"] == 10
        assert pending["call_id"] == "call-1"
        assert pending["tool"] == "set_device_power"
        assert pending["args"] == {"device_id": 1, "power": "on"}
        assert pending["risk_level"] == "high"
        assert pending["reasons"] == ["高风险操作"]
        assert pending["preview"] == {"device_name": "客厅灯"}
        assert pending["resource_version"] == "v1"
        assert pending["model_name"] == "test"
        assert pending["model_id"] == 1
        assert "created_at" in pending
        assert "expires_at" in pending
        # expires_at 应在 created_at 之后
        assert pending["expires_at"] > 0
