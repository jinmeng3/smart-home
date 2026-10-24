"""鉴权与账户相关接口测试。

覆盖文档 §1 中的所有端点。
"""
from __future__ import annotations

import io


# === /auth/* ====


def test_register_creates_user(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "alice", "email": "alice@example.com", "password": "StrongP@ss1"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["code"] == 0
    assert body["message"] == "created"
    data = body["data"]
    assert data["tokenType"] == "Bearer"
    assert data["expiresIn"] > 0
    assert data["user"]["email"] == "alice@example.com"


def test_register_rejects_short_password(client):
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "short"},
    )
    assert resp.status_code == 422


def test_register_rejects_duplicate_email(client, make_user):
    make_user(email="dup@example.com")
    resp = client.post(
        "/api/auth/register",
        json={"username": "bob", "email": "dup@example.com", "password": "StrongP@ss1"},
    )
    assert resp.status_code == 409


def test_login_success(client, make_user):
    make_user(email="login@example.com", password="StrongP@ss1")
    resp = client.post(
        "/api/auth/login",
        json={"account": "login@example.com", "password": "StrongP@ss1"},
    )
    assert resp.status_code == 200
    assert resp.json()["data"]["accessToken"]


def test_login_strips_account(client, make_user):
    make_user(email="trim@example.com")
    resp = client.post(
        "/api/auth/login",
        json={"account": "  trim@example.com  ", "password": "StrongP@ss1"},
    )
    assert resp.status_code == 200


def test_login_wrong_password(client, make_user):
    make_user(email="wrong@example.com", password="StrongP@ss1")
    resp = client.post(
        "/api/auth/login",
        json={"account": "wrong@example.com", "password": "wrongpass"},
    )
    assert resp.status_code == 401


def test_login_locked_after_max_attempts(client, make_user):
    """5 次失败后账号被锁定，后续请求应返 423 且带 remaining_seconds。"""
    from app.core.config import get_settings

    make_user(email="locked@example.com", password="StrongP@ss1")
    max_attempts = get_settings().max_failed_login_attempts
    for _ in range(max_attempts):
        client.post(
            "/api/auth/login",
            json={"account": "locked@example.com", "password": "wrongpass"},
        )
    resp = client.post(
        "/api/auth/login",
        json={"account": "locked@example.com", "password": "StrongP@ss1"},
    )
    assert resp.status_code == 423
    body = resp.json()
    # data 透传了剩余秒数与锁定时间，供前端“X 分钟后重试”提示使用
    assert body["code"] == 42300
    data = body.get("data") or {}
    assert isinstance(data.get("remaining_seconds"), int)
    assert data["remaining_seconds"] > 0
    assert isinstance(data.get("locked_until"), str)
    assert data.get("message")  # 业务 message 也透传


def test_logout_returns_ok(make_user):
    from fastapi.testclient import TestClient
    from app.main import app

    _, headers = make_user(email="logout@example.com")
    with TestClient(app) as c:
        resp = c.post("/api/auth/logout", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "logged out"


def test_protected_route_without_token(client):
    resp = client.get("/api/account/me")
    assert resp.status_code == 401


# === /account/me ====


def test_get_me(make_user):
    _, headers = make_user(email="me@example.com", name="me")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.get("/api/account/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["email"] == "me@example.com"
    assert data["name"] == "me"


def test_update_me_changes_name_and_email(make_user):
    _, headers = make_user(email="upd@example.com", name="orig")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.patch(
            "/api/account/me",
            headers=headers,
            json={"name": "renamed", "email": "new@example.com"},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "renamed"
    assert resp.json()["data"]["email"] == "new@example.com"


def test_update_me_email_conflict(make_user):
    make_user(email="taken@example.com")
    _, headers = make_user(email="taker@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.patch(
            "/api/account/me",
            headers=headers,
            json={"email": "taken@example.com"},
        )
    assert resp.status_code == 409


def test_update_me_requires_field(make_user):
    _, headers = make_user(email="empty@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.patch("/api/account/me", headers=headers, json={})
    assert resp.status_code == 422


def test_update_me_rejects_null_field(make_user):
    _, headers = make_user(email="null@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.patch(
            "/api/account/me",
            headers=headers,
            json={"name": None, "email": None},
        )
    assert resp.status_code == 422


def test_preferences_default(make_user):
    _, headers = make_user(email="pref@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.get("/api/account/me/preferences", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["appearance"]["themeMode"] == "light"
    assert data["aiAssistant"]["language"] == "zh-CN"


def test_preferences_round_trip(make_user):
    _, headers = make_user(email="pref2@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    payload = {
        "appearance": {
            "themeMode": "dark",
            "fontSize": "large",
            "animationsEnabled": False,
            "sidebarCollapsed": True,
            "performanceMode": True,
        },
        "aiAssistant": {
            "language": "en-US",
            "detailLevel": 30,
            "autoExecuteLowRisk": True,
            "confirmHighRisk": False,
        },
        "notifications": {
            "deviceOffline": False,
            "securityAlerts": True,
            "automationResults": False,
            "quietStart": "00:00",
            "quietEnd": "08:00",
        },
        "security": {"twoFactorEnabled": False},
        "backup": {"autoBackup": False},
    }

    with TestClient(app) as c:
        put = c.put("/api/account/me/preferences", headers=headers, json=payload)
        assert put.status_code == 200
        get = c.get("/api/account/me/preferences", headers=headers)
        assert get.json()["data"]["appearance"]["themeMode"] == "dark"


def test_avatar_upload_and_delete(make_user, _isolated_dirs):
    _, headers = make_user(email="avatar@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    avatar_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\rIDATx\xdac\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\xc7\xb6\x9e\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with TestClient(app) as c:
        resp = c.post(
            "/api/account/me/avatar",
            headers=headers,
            files={"avatar": ("avatar.png", io.BytesIO(avatar_bytes), "image/png")},
        )
    assert resp.status_code == 200
    avatar_url = resp.json()["data"]["avatar_url"]
    assert avatar_url.startswith("/uploads/avatars/")

    # 文件确实写到磁盘
    file_path = _isolated_dirs["uploads"] / "avatars" / avatar_url.split("/")[-1]
    assert file_path.exists()

    with TestClient(app) as c:
        resp = c.delete("/api/account/me/avatar", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["data"]["avatar_url"] is None


def test_avatar_upload_rejects_bad_type(make_user):
    _, headers = make_user(email="bad-avatar@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.post(
            "/api/account/me/avatar",
            headers=headers,
            files={"avatar": ("avatar.gif", io.BytesIO(b"GIF89a"), "image/gif")},
        )
    assert resp.status_code == 415


# === /account/me/security ====


def test_security_meta_after_login(make_user):
    _, headers = make_user(email="sec@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.get("/api/account/me/security", headers=headers)
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert any(d["is_current"] for d in data["devices"])


def test_add_security_log(make_user):
    _, headers = make_user(email="log@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.post(
            "/api/account/me/security/logs",
            headers=headers,
            json={"title": "Login", "detail": "Logged in from new device"},
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["title"] == "Login"


def test_patch_device_trust_and_revoke(make_user):
    _, headers = make_user(email="trust@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        # 桌面设备登录（current）
        meta_before = c.get("/api/account/me/security", headers=headers).json()["data"]
        desktop_device = next(d for d in meta_before["devices"] if d["is_current"])

        # 以移动端 UA 登录，生成新的 location 记录
        mobile_login = c.post(
            "/api/auth/login",
            headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile/15E148"},
            json={"account": "trust@example.com", "password": "StrongP@ss1"},
        )
        assert mobile_login.status_code == 200
        mobile_token = mobile_login.json()["data"]["accessToken"]
        mobile_headers = {"Authorization": f"Bearer {mobile_token}"}

        # 当前 mobile 设备视图下，desktop 变成「非 current」
        meta = c.get("/api/account/me/security", headers=mobile_headers).json()["data"]
        desktop = next(d for d in meta["devices"] if d["id"] == desktop_device["id"])
        mobile = next(d for d in meta["devices"] if d["is_current"])
        assert desktop["id"] != mobile["id"]
        assert not desktop["is_current"]

        # 切换 trust 标记
        patch = c.patch(
            f"/api/account/me/security/devices/{desktop['id']}",
            headers=mobile_headers,
            json={"trusted": True},
        )
        assert patch.status_code == 200
        assert patch.json()["data"]["trusted"] is True

        # 当前 mobile 设备不能移除
        bad = c.delete(
            f"/api/account/me/security/devices/{mobile['id']}",
            headers=mobile_headers,
        )
        assert bad.status_code == 422

        # 非当前 desktop 设备可移除
        ok = c.delete(
            f"/api/account/me/security/devices/{desktop['id']}",
            headers=mobile_headers,
        )
        assert ok.status_code == 204


def test_revoke_missing_device_returns_404(make_user):
    _, headers = make_user(email="missing@example.com")
    from fastapi.testclient import TestClient
    from app.main import app

    with TestClient(app) as c:
        resp = c.delete("/api/account/me/security/devices/9999", headers=headers)
    assert resp.status_code == 404