"""AI 模型配置接口测试。

覆盖文档 §2 中的端点。这些接口的 ping 路径会真正发起网络请求，
所以只测试 CRUD 与本地校验，不测试 ping。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _new_ctx(make_household):
    return make_household()


def test_list_providers():
    """无需登录即可列出供应商。"""
    with TestClient(app) as c:
        resp = c.get("/api/ai_model/providers")
    assert resp.status_code == 200
    data = resp.json()["data"]
    # Settings 默认支持 openai / deepseek
    assert any(p["id"] == "openai" for p in data)


def test_ping_requires_login():
    with TestClient(app) as c:
        resp = c.post(
            "/api/ai_model/ping",
            json={
                "name": "test",
                "provider": "openai",
                "api_endpoint": "https://x",
            },
        )
    assert resp.status_code == 401


def test_ping_invalid_payload(make_user):
    _, headers = make_user(email="ai@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/ai_model/ping",
            headers=headers,
            json={"name": ""},  # 缺 provider / endpoint
        )
    assert resp.status_code == 422


def _model_payload(name="m1", **overrides):
    base = {
        "name": name,
        "provider": "openai",
        "api": "openai-completions",
        "api_endpoint": "https://api.openai.com/v1",
        "api_key": "sk-test",
        "parameters": {"model": "gpt-4o-mini"},
        "max_tokens": 4096,
        "is_active": True,
    }
    base.update(overrides)
    return base


def test_create_and_list_models(make_user):
    _, headers = make_user(email="ai-list@example.com")
    with TestClient(app) as c:
        created = c.post(
            "/api/ai_model/model", headers=headers, json=_model_payload()
        )
    assert created.status_code == 201
    assert created.json()["data"]["is_active"] is True

    with TestClient(app) as c:
        listed = c.get("/api/ai_model/models", headers=headers)
        active = c.get("/api/ai_model/model", headers=headers)
    assert listed.status_code == 200
    item = listed.json()["data"][0]
    assert (item.get("has_api_key") or item.get("hasApiKey")) is True
    assert active.status_code == 200
    assert active.json()["data"]["name"] == "m1"


def test_activate_model(make_user):
    _, headers = make_user(email="ai-activate@example.com")
    with TestClient(app) as c:
        a = c.post(
            "/api/ai_model/model",
            headers=headers,
            json=_model_payload(name="a", is_active=True),
        )
        b = c.post(
            "/api/ai_model/model",
            headers=headers,
            json=_model_payload(name="b", is_active=False),
        )
        bid = b.json()["data"]["id"]
        resp = c.post(
            f"/api/ai_model/models/{bid}/activate", headers=headers
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["is_active"] is True


def test_update_model_by_id(make_user):
    _, headers = make_user(email="ai-update@example.com")
    with TestClient(app) as c:
        created = c.post(
            "/api/ai_model/model", headers=headers, json=_model_payload()
        )
        mid = created.json()["data"]["id"]
        resp = c.patch(
            f"/api/ai_model/models/{mid}",
            headers=headers,
            json={"name": "renamed", "temperature": 0.3},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "renamed"


def test_update_model_requires_field(make_user):
    _, headers = make_user(email="ai-empty@example.com")
    with TestClient(app) as c:
        created = c.post(
            "/api/ai_model/model", headers=headers, json=_model_payload()
        )
        mid = created.json()["data"]["id"]
        resp = c.patch(
            f"/api/ai_model/models/{mid}", headers=headers, json={}
        )
    assert resp.status_code == 422


def test_update_active_model(make_user):
    _, headers = make_user(email="ai-active@example.com")
    with TestClient(app) as c:
        c.post("/api/ai_model/model", headers=headers, json=_model_payload())
        resp = c.patch(
            "/api/ai_model/model",
            headers=headers,
            json={"description": "updated"},
        )
    assert resp.status_code == 200


def test_delete_active_model(make_user):
    _, headers = make_user(email="ai-del@example.com")
    with TestClient(app) as c:
        c.post("/api/ai_model/model", headers=headers, json=_model_payload())
        resp = c.delete("/api/ai_model/model", headers=headers)
    assert resp.status_code == 204


def test_delete_model_by_id(make_user):
    _, headers = make_user(email="ai-del2@example.com")
    with TestClient(app) as c:
        c.post(
            "/api/ai_model/model",
            headers=headers,
            json=_model_payload(name="inactive", is_active=False),
        )
        listed = c.get("/api/ai_model/models", headers=headers).json()["data"]
        target = next(m for m in listed if m["name"] == "inactive")
        resp = c.delete(
            f"/api/ai_model/models/{target['id']}", headers=headers
        )
    assert resp.status_code == 204


def test_create_model_protocol_compat(make_user):
    """compat 字段验证：必须能被对应协议的 schema 接受。"""
    _, headers = make_user(email="compat@example.com")
    with TestClient(app) as c:
        # OK：openai-completions 支持 force_json_mode
        ok = c.post(
            "/api/ai_model/model",
            headers=headers,
            json=_model_payload(
                api="openai-completions",
                compat={"force_json_mode": True},
            ),
        )
        assert ok.status_code == 201

        # OK：openai-responses 支持 include_reasoning
        ok2 = c.post(
            "/api/ai_model/model",
            headers=headers,
            json=_model_payload(
                name="oai-resp",
                api="openai-responses",
                compat={"include_reasoning": True},
            ),
        )
        assert ok2.status_code == 201

        # 非法：未知 API 协议
        bad = c.post(
            "/api/ai_model/model",
            headers=headers,
            json=_model_payload(name="bad", api="unknown-protocol"),
        )
        assert bad.status_code == 422