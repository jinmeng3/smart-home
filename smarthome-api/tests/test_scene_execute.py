"""场景执行写工具的审批失效边界测试。"""

from app.agents.context import AgentContext
from app.agents.tools.execute import scenes as scenes_mod
from fastapi import HTTPException


def _context() -> AgentContext:
    return AgentContext(
        user_id=1,
        household_id=1,
        session_id=1,
        auto_execute_low_risk=False,
        confirm_high_risk=True,
    )


def _pending() -> dict:
    return {"approval_id": "a1", "resource_version": "v1"}


def test_execute_scene_returns_stale_when_scene_deleted(monkeypatch):
    def boom(db=None, context=None, scene_id=None):
        raise HTTPException(status_code=404, detail="场景不存在")

    monkeypatch.setattr(scenes_mod, "classify_scene_execution", boom)

    result = scenes_mod.execute_scene_operation(
        db=None, context=_context(), args={"scene_id": "s1"}, pending=_pending()
    )
    assert result["ok"] is False
    assert result["code"] == "AGENT_APPROVAL_STALE"


def test_execute_scene_returns_stale_when_scene_disabled(monkeypatch):
    class FakeDecision:
        preview = {"steps": []}
        resource_version = "v1"

    monkeypatch.setattr(
        scenes_mod,
        "classify_scene_execution",
        lambda db, context, scene_id: FakeDecision(),
    )

    def boom(**kwargs):
        raise HTTPException(status_code=409, detail="场景已停用")

    monkeypatch.setattr(scenes_mod, "run_scene_service", boom)

    result = scenes_mod.execute_scene_operation(
        db=None, context=_context(), args={"scene_id": "s1"}, pending=_pending()
    )
    assert result["ok"] is False
    assert result["code"] == "AGENT_APPROVAL_STALE"


def test_execute_scene_returns_stale_on_version_change(monkeypatch):
    class FakeDecision:
        preview = {"steps": []}
        resource_version = "v2"

    monkeypatch.setattr(
        scenes_mod,
        "classify_scene_execution",
        lambda db, context, scene_id: FakeDecision(),
    )

    result = scenes_mod.execute_scene_operation(
        db=None, context=_context(), args={"scene_id": "s1"}, pending=_pending()
    )
    assert result["ok"] is False
    assert result["code"] == "AGENT_APPROVAL_STALE"
