"""聊天会话接口测试。

不发起流式补全 / Agent 调用（这些需要 OpenAI/LLM 网络）。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_create_and_list_session(make_user):
    _, headers = make_user(email="chat@example.com")
    with TestClient(app) as c:
        create = c.post(
            "/api/chat/sessions?mode=chat&model_name=test", headers=headers
        )
        assert create.status_code == 201
        sid = create.json()["data"]["id"]

        listed = c.get("/api/chat/sessions", headers=headers)
        assert listed.status_code == 200
        assert listed.json()["data"][0]["id"] == sid


def test_create_session_default_mode(make_user):
    _, headers = make_user(email="chat2@example.com")
    with TestClient(app) as c:
        resp = c.post("/api/chat/sessions", headers=headers)
    assert resp.status_code == 201
    assert resp.json()["data"]["mode"] == "agent"


def test_update_session_mode_and_model(make_user):
    _, headers = make_user(email="chat3@example.com")
    with TestClient(app) as c:
        sid = c.post(
            "/api/chat/sessions", headers=headers
        ).json()["data"]["id"]

        patch = c.patch(
            f"/api/chat/sessions/{sid}/mode",
            headers=headers,
            json={"mode": "chat"},
        )
        assert patch.status_code == 200
        assert patch.json()["data"]["mode"] == "chat"

        patch2 = c.patch(
            f"/api/chat/sessions/{sid}/model",
            headers=headers,
            json={"model_name": "my-model"},
        )
        assert patch2.status_code == 200
        assert patch2.json()["data"]["model_name"] == "my-model"


def test_list_messages_empty(make_user):
    _, headers = make_user(email="chat4@example.com")
    with TestClient(app) as c:
        sid = c.post(
            "/api/chat/sessions", headers=headers
        ).json()["data"]["id"]
        resp = c.get(
            f"/api/chat/sessions/{sid}/messages", headers=headers
        )
    assert resp.status_code == 200
    assert resp.json()["data"] == []


def test_delete_session(make_user):
    _, headers = make_user(email="chat5@example.com")
    with TestClient(app) as c:
        sid = c.post(
            "/api/chat/sessions", headers=headers
        ).json()["data"]["id"]
        resp = c.delete(
            f"/api/chat/sessions/{sid}", headers=headers
        )
    assert resp.status_code == 204


def test_completions_validates_payload(make_user):
    _, headers = make_user(email="chat6@example.com")
    with TestClient(app) as c:
        # 缺少 messages
        bad = c.post(
            "/api/chat/completions", headers=headers, json={"model": "x"}
        )
        assert bad.status_code == 422

        # 缺 messages 但 stream=false 应能返回 ApiResponse
        sid = c.post(
            "/api/chat/sessions", headers=headers
        ).json()["data"]["id"]
        # 非流式 + 不会发到模型，因为没有激活 AI 模型 → 应该报错（500xx）或被服务拦下
        # 这里只保证 endpoint 接受合法 schema
        resp = c.post(
            "/api/chat/completions",
            headers=headers,
            json={
                "model": "x",
                "messages": [{"role": "user", "content": "hi"}],
                "sessionId": sid,
                "stream": False,
            },
        )
        # 不论成功或失败，不应是 422 schema 错
        assert resp.status_code != 422


def test_completion_message_role_validation(make_user):
    _, headers = make_user(email="chat7@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/chat/completions",
            headers=headers,
            json={
                "model": "x",
                "messages": [{"role": "wizard", "content": "hi"}],
                "stream": False,
            },
        )
    assert resp.status_code == 422