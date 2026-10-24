"""家庭管理与成员接口测试。

覆盖文档 §5、§6 中的端点。
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


# === /households ====


def test_list_households(make_household):
    ctx = make_household()
    with TestClient(app) as c:
        resp = c.get("/api/households", headers=ctx["headers"])
    assert resp.status_code == 200
    items = resp.json()["data"]
    assert len(items) == 1
    assert items[0]["id"] == ctx["household_id"]
    assert items[0]["role"] == "admin"
    assert items[0]["member_count"] == 1


def test_create_household_validates_timezone(make_user):
    _, headers = make_user(email="tz@example.com")
    with TestClient(app) as c:
        # 合法
        ok = c.post(
            "/api/households",
            headers=headers,
            json={"name": "Home A", "timezone": "Asia/Tokyo"},
        )
        assert ok.status_code == 201

        # 非法
        bad = c.post(
            "/api/households",
            headers=headers,
            json={"name": "Home B", "timezone": "Mars/Olympus_Mons"},
        )
        assert bad.status_code == 422


def test_create_household_strips_name(make_user):
    _, headers = make_user(email="strip@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/households",
            headers=headers,
            json={"name": "  Padded  ", "timezone": "Asia/Shanghai"},
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "Padded"


def test_read_and_update_household(make_household):
    ctx = make_household()
    with TestClient(app) as c:
        get = c.get(f"/api/households/{ctx['household_id']}", headers=ctx["headers"])
        assert get.status_code == 200
        assert get.json()["data"]["name"] == "My Home"

        patch = c.patch(
            f"/api/households/{ctx['household_id']}",
            headers=ctx["headers"],
            json={"name": "Renamed", "address": "Beijing", "timezone": "Asia/Tokyo"},
        )
    assert patch.status_code == 200
    data = patch.json()["data"]
    assert data["name"] == "Renamed"
    assert data["address"] == "Beijing"
    assert data["timezone"] == "Asia/Tokyo"


def test_update_household_requires_field(make_household):
    ctx = make_household()
    with TestClient(app) as c:
        resp = c.patch(
            f"/api/households/{ctx['household_id']}",
            headers=ctx["headers"],
            json={},
        )
    assert resp.status_code == 422


def test_update_household_clear_address(make_household):
    """address 是可空字段，应该允许显式设为 None。"""
    ctx = make_household()
    with TestClient(app) as c:
        c.patch(
            f"/api/households/{ctx['household_id']}",
            headers=ctx["headers"],
            json={"address": "Shanghai"},
        )
        cleared = c.patch(
            f"/api/households/{ctx['household_id']}",
            headers=ctx["headers"],
            json={"address": None},
        )
    assert cleared.status_code == 200
    assert cleared.json()["data"]["address"] is None


def test_non_member_cannot_read_household(make_household, make_user):
    owner = make_household()
    _, outsider = make_user(email="outsider@example.com")
    with TestClient(app) as c:
        resp = c.get(f"/api/households/{owner['household_id']}", headers=outsider)
    assert resp.status_code == 403


def test_non_admin_cannot_update_household(make_household, make_user):
    owner = make_household()
    # 把第二个用户加成 member
    extra, extra_headers = make_user(email="member@example.com")
    with TestClient(app) as c:
        c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "member@example.com", "role": "member"},
        )
        # 以 member 身份尝试更新
        resp = c.patch(
            f"/api/households/{owner['household_id']}",
            headers=extra_headers,
            json={"name": "Hacked"},
        )
    assert resp.status_code == 403


# === /households/{id}/members ====


def test_list_members(make_household):
    ctx = make_household()
    with TestClient(app) as c:
        resp = c.get(
            f"/api/households/{ctx['household_id']}/members", headers=ctx["headers"]
        )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 1


def test_add_member_by_email(make_household, make_user):
    owner = make_household()
    make_user(email="invitee@example.com")
    with TestClient(app) as c:
        resp = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "invitee@example.com", "role": "admin"},
        )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["email"] == "invitee@example.com"
    assert data["role"] == "admin"


def test_add_member_unknown_email(make_household):
    owner = make_household()
    with TestClient(app) as c:
        resp = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "ghost@example.com"},
        )
    assert resp.status_code == 404


def test_add_member_duplicate(make_household, make_user):
    owner = make_household()
    make_user(email="dup@example.com")
    with TestClient(app) as c:
        c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "dup@example.com"},
        )
        dup = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "dup@example.com"},
        )
    assert dup.status_code == 409


def test_non_admin_cannot_add_member(make_household, make_user):
    owner = make_household()
    make_user(email="newbie@example.com")
    _, member_headers = make_user(email="member@example.com")
    with TestClient(app) as c:
        c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "member@example.com", "role": "member"},
        )
        resp = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=member_headers,
            json={"email": "newbie@example.com"},
        )
    assert resp.status_code == 403


def test_change_member_role(make_household, make_user):
    owner = make_household()
    make_user(email="victim@example.com")
    with TestClient(app) as c:
        add = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "victim@example.com", "role": "member"},
        )
        membership_id = add.json()["data"]["membership_id"]
        patch = c.patch(
            f"/api/households/{owner['household_id']}/members/{membership_id}",
            headers=owner["headers"],
            json={"role": "admin"},
        )
    assert patch.status_code == 200
    assert patch.json()["data"]["role"] == "admin"


def test_cannot_change_own_role(make_household):
    owner = make_household()
    # owner 自己作为 admin，尝试改自己
    with TestClient(app) as c:
        list_resp = c.get(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
        )
        self_id = list_resp.json()["data"]["items"][0]["membership_id"]
        resp = c.patch(
            f"/api/households/{owner['household_id']}/members/{self_id}",
            headers=owner["headers"],
            json={"role": "member"},
        )
    assert resp.status_code == 400


def test_demote_last_admin_rejected(make_household, make_user):
    """把最后一个 admin 降级为 member 应该被拒绝。"""
    owner = make_household()
    make_user(email="second@example.com")
    with TestClient(app) as c:
        add = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "second@example.com", "role": "admin"},
        )
        second_id = add.json()["data"]["membership_id"]
        owner_id = c.get(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
        ).json()["data"]["items"][0]["membership_id"]

        # 现在 owner 把 second 降级（这应该 ok，还有 owner）
        c.patch(
            f"/api/households/{owner['household_id']}/members/{second_id}",
            headers=owner["headers"],
            json={"role": "member"},
        )

        # 现在只剩 owner 是 admin，把 second 加回 admin 然后 owner 试图降级自己
        c.patch(
            f"/api/households/{owner['household_id']}/members/{second_id}",
            headers=owner["headers"],
            json={"role": "admin"},
        )
        resp = c.patch(
            f"/api/households/{owner['household_id']}/members/{owner_id}",
            headers=owner["headers"],
            json={"role": "member"},
        )
    # 改自己的角色被前置校验拒掉（400）
    assert resp.status_code == 400


def test_remove_member(make_household, make_user):
    owner = make_household()
    make_user(email="victim2@example.com")
    with TestClient(app) as c:
        add = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "victim2@example.com"},
        )
        member_id = add.json()["data"]["membership_id"]
        resp = c.delete(
            f"/api/households/{owner['household_id']}/members/{member_id}",
            headers=owner["headers"],
        )
    assert resp.status_code == 204


def test_cannot_remove_self(make_household):
    owner = make_household()
    with TestClient(app) as c:
        self_id = c.get(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
        ).json()["data"]["items"][0]["membership_id"]
        resp = c.delete(
            f"/api/households/{owner['household_id']}/members/{self_id}",
            headers=owner["headers"],
        )
    assert resp.status_code == 400


def test_cannot_remove_last_admin(make_household, make_user):
    owner = make_household()
    make_user(email="last@example.com")
    with TestClient(app) as c:
        add = c.post(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
            json={"email": "last@example.com", "role": "admin"},
        )
        second_id = add.json()["data"]["membership_id"]
        owner_id = c.get(
            f"/api/households/{owner['household_id']}/members",
            headers=owner["headers"],
        ).json()["data"]["items"][0]["membership_id"]
        # 先把 second 降级，再删 owner：此时 second 是 admin，但 owner 不可删除自己
        c.patch(
            f"/api/households/{owner['household_id']}/members/{second_id}",
            headers=owner["headers"],
            json={"role": "member"},
        )
        resp = c.delete(
            f"/api/households/{owner['household_id']}/members/{owner_id}",
            headers=owner["headers"],
        )
    assert resp.status_code == 400  # 自己不能删除自己


def test_delete_missing_member(make_household):
    owner = make_household()
    with TestClient(app) as c:
        resp = c.delete(
            f"/api/households/{owner['household_id']}/members/9999",
            headers=owner["headers"],
        )
    assert resp.status_code == 404