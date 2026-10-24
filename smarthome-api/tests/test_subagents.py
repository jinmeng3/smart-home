"""子 Agent 基础设施（P0）单元测试。"""

import pytest

from app.agents.context import AgentContext
from app.agents.subagents import (
    DOMAIN_KEYWORDS,
    SubAgentInput,
    SubAgentOutput,
    is_write_domain,
    resolve_delegated_domain,
    route_intent,
)
from app.agents.tools import (
    DOMAIN_TOOL_NAMES,
    DOMAIN_WRITE_TOOL_NAMES,
    WRITE_TOOL_NAMES,
    get_domain_tools,
    get_household_tools,
)


def make_context() -> AgentContext:
    return AgentContext(
        user_id=1,
        household_id=1,
        session_id=1,
        auto_execute_low_risk=False,
        confirm_high_risk=True,
    )


# === 路由 ===


def test_route_intent_single_domain():
    assert route_intent("客厅的灯是什么状态") == ["device"]
    assert route_intent("执行回家模式") == ["scene"]
    assert route_intent("每天早上7点打开窗帘") == ["automation"]


def test_route_intent_composite_intent():
    tags = route_intent("打开客厅灯并锁上大门")
    assert "device" in tags
    assert "security" in tags


def test_route_intent_general_fallback():
    assert route_intent("今天天气怎么样") == ["general"]
    assert route_intent("") == ["general"]


def test_route_intent_preserves_declaration_order():
    # 复合意图按关键词表声明顺序返回（device 在 security 之前）
    assert route_intent("打开客厅灯并锁上大门") == ["device", "security"]


def test_resolve_delegated_domain_single_read_only():
    assert resolve_delegated_domain("客厅的灯是什么状态") == "device"


def test_resolve_delegated_domain_composite_returns_none():
    assert resolve_delegated_domain("打开客厅灯并锁上大门") is None


def test_resolve_delegated_domain_general_returns_none():
    assert resolve_delegated_domain("今天天气怎么样") is None
    assert resolve_delegated_domain("") is None


def test_resolve_delegated_domain_automation_write():
    assert resolve_delegated_domain("每天早上7点打开窗帘") == "automation"


def test_resolve_delegated_domain_scene_write():
    assert resolve_delegated_domain("执行回家模式") == "scene"


def test_resolve_delegated_domain_security_read():
    assert resolve_delegated_domain("查一下安防情况") == "security"


def test_is_write_domain():
    assert is_write_domain("automation") is True
    assert is_write_domain("scene") is True
    assert is_write_domain("device") is False
    assert is_write_domain("security") is False
    assert is_write_domain(None) is False


def test_domain_keywords_covers_all_tool_domains():
    # 每个工具领域都有对应的路由关键词表
    assert set(DOMAIN_TOOL_NAMES) == set(DOMAIN_KEYWORDS)


# === 领域工具过滤 ===


def test_get_domain_tools_returns_only_domain_tools():
    ctx = make_context()
    for domain, expected in DOMAIN_TOOL_NAMES.items():
        tools = get_domain_tools(domain, ctx, None)
        assert {tool.name for tool in tools} == expected


def test_domain_tools_are_read_only():
    for domain, names in DOMAIN_TOOL_NAMES.items():
        assert not (names & WRITE_TOOL_NAMES), f"{domain} 不应包含写工具"


def test_domain_tool_names_are_valid():
    ctx = make_context()
    all_names = {tool.name for tool in get_household_tools(ctx, None)}
    for names in DOMAIN_TOOL_NAMES.values():
        assert names <= all_names


def test_get_domain_tools_unknown_domain_is_empty():
    ctx = make_context()
    assert get_domain_tools("not-a-domain", ctx, None) == []


def test_get_domain_tools_include_write():
    ctx = make_context()
    read_only = {tool.name for tool in get_domain_tools("automation", ctx, None)}
    assert read_only == DOMAIN_TOOL_NAMES["automation"]
    assert not (read_only & WRITE_TOOL_NAMES)

    with_write = {
        tool.name
        for tool in get_domain_tools("automation", ctx, None, include_write=True)
    }
    assert DOMAIN_WRITE_TOOL_NAMES["automation"] <= with_write


def test_domain_write_tools_are_valid():
    ctx = make_context()
    all_names = {tool.name for tool in get_household_tools(ctx, None)}
    for names in DOMAIN_WRITE_TOOL_NAMES.values():
        assert names <= all_names
        assert names <= WRITE_TOOL_NAMES


# === 契约 ===


def test_subagent_input_defaults():
    inp = SubAgentInput(
        household_id=1, session_id=1, user_id=1, domain="device", task="查设备"
    )
    assert inp.max_tool_calls == 5
    assert inp.timeout_seconds == 8.0
    assert inp.shared_context == {}
    assert inp.session_summary == ""


def test_subagent_input_rejects_invalid_timeout():
    with pytest.raises(Exception):
        SubAgentInput(
            household_id=1,
            session_id=1,
            user_id=1,
            domain="device",
            task="查设备",
            timeout_seconds=0,
        )


def test_subagent_output_defaults():
    out = SubAgentOutput(domain="device", response_text="ok")
    assert out.write_proposals == []
    assert out.structured_data == {}
    assert out.fallback_needed is False
    assert out.error is None


def test_audit_recorder_subagent_events(tmp_path):
    import json

    from app.agents.audit.recorder import AuditRecorder

    recorder = AuditRecorder(log_dir=tmp_path)
    recorder.record_subagent_start(run_id="r1", domain="device", task="查设备")
    recorder.record_subagent_end(
        run_id="r1",
        domain="device",
        status="completed",
        summary="设备状态正常",
        duration_ms=12,
        usage={"input": 10, "output": 5},
    )
    recorder.close()

    files = list(tmp_path.glob("audit_*.json"))
    assert len(files) == 1
    events = [
        json.loads(line) for line in files[0].read_text(encoding="utf-8").splitlines()
    ]
    assert [e["event"] for e in events] == ["subagent_start", "subagent_end"]
    assert events[0]["domain"] == "device"
    assert events[1]["status"] == "completed"
