"""夹具烟囱测试：确认测试基础设施可用。"""
from __future__ import annotations


def test_app_imports(client):
    resp = client.get("/openapi.json")
    assert resp.status_code == 200
    paths = resp.json()["paths"]
    assert "/api/auth/login" in paths


def test_register_and_login(client, make_user):
    data, headers = make_user(email="smoke@example.com", name="smoke")
    assert data["user"]["email"] == "smoke@example.com"

    resp = client.post(
        "/api/auth/login",
        json={"account": "smoke@example.com", "password": "StrongP@ss1"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["accessToken"]


def test_create_household(make_household):
    ctx = make_household()
    assert ctx["household_id"] > 0
    assert "Authorization" in ctx["headers"]