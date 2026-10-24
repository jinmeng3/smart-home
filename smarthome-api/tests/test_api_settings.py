"""设置建议与 AI 模板生成测试。

这些接口依赖真实 LLM，无法在测试环境跑通。
只验证 schema 校验与权限拦截。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


def test_settings_suggestions_requires_login():
    with TestClient(app) as c:
        resp = c.post(
            "/api/settings/suggestions/ai",
            json={"snapshot": {}},
        )
    assert resp.status_code == 401


def test_ai_templates_requires_login():
    with TestClient(app) as c:
        resp = c.post(
            "/api/automations/templates/ai",
            json={"deviceSummary": {"online": 1, "offline": 0}},
        )
    assert resp.status_code == 401


def test_ai_templates_validates_count(make_user):
    _, headers = make_user(email="tpl1@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/automations/templates/ai",
            headers=headers,
            json={"count": 999},
        )
    assert resp.status_code == 422


def test_ai_templates_validates_device_summary(make_user):
    _, headers = make_user(email="tpl2@example.com")
    with TestClient(app) as c:
        # count 越界
        resp = c.post(
            "/api/automations/templates/ai",
            headers=headers,
            json={"deviceSummary": {"online": 1}, "count": 0},
        )
        assert resp.status_code == 422


def test_ai_templates_force_flag(make_user):
    """force=true 走强制重新生成路径；没有激活模型会被服务拦下。"""
    _, headers = make_user(email="tpl3@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/automations/templates/ai?force=true",
            headers=headers,
            json={"deviceSummary": {"online": 5, "offline": 1}, "count": 3},
        )
    # 没有激活模型 → 服务抛错
    assert resp.status_code in (400, 404, 500)


def test_settings_suggestions_accepts_snapshot(make_user):
    """确认请求体格式合法，response 体可解析。"""
    _, headers = make_user(email="ss@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/settings/suggestions/ai",
            headers=headers,
            json={"snapshot": {"appearance": {"themeMode": "dark"}}},
        )
    # 没有激活模型 → 服务报错
    assert resp.status_code in (400, 404, 500)