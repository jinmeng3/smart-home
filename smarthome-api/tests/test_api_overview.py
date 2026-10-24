"""家庭概览、巡检、日程、同步任务接口测试。

覆盖文档 §11 中的端点。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def ctx(make_household):
    return make_household()


def test_overview(ctx):
    with TestClient(app) as c:
        resp = c.get(
            f"/api/households/{ctx['household_id']}/overview",
            headers=ctx["headers"],
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "summary" in data
    assert "home_status" in data


def test_overview_requires_member(make_household, make_user):
    owner = make_household()
    _, outsider = make_user(email="out@example.com")
    with TestClient(app) as c:
        resp = c.get(
            f"/api/households/{owner['household_id']}/overview",
            headers=outsider,
        )
    assert resp.status_code == 403


def test_list_household_devices(ctx):
    with TestClient(app) as c:
        # 设备绑定需要房间存在
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "Living"})
        c.post(
            "/api/devices",
            headers=ctx["headers"],
            json={
                "name": "L",
                "room": "Living",
                "type": "light",
                "brand": "P",
                "connection": "Matter",
                "deviceId": "M-1",
            },
        )
        resp = c.get(
            f"/api/households/{ctx['household_id']}/devices",
            headers=ctx["headers"],
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


def test_today_energy(ctx):
    with TestClient(app) as c:
        resp = c.get(
            f"/api/households/{ctx['household_id']}/energy/today",
            headers=ctx["headers"],
        )
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert "energy_kwh" in data


def test_execute_mode(ctx):
    with TestClient(app) as c:
        resp = c.post(
            "/api/overview/modes/execute",
            headers=ctx["headers"],
            json={
                "mode": "home",
                "roomIds": [],
                "runAutomations": False,
                "idempotencyKey": "test-key-1",
            },
        )
    assert resp.status_code == 202


def test_execute_mode_invalid(ctx):
    with TestClient(app) as c:
        resp = c.post(
            "/api/overview/modes/execute",
            headers=ctx["headers"],
            json={
                "mode": "vacation",
                "idempotencyKey": "test-key-2",
            },
        )
    assert resp.status_code == 422


def test_create_and_get_inspection(ctx):
    with TestClient(app) as c:
        create = c.post(
            "/api/inspections",
            headers=ctx["headers"],
            json={
                "scope": "all",
                "roomIds": [],
                "deviceTypes": [],
                "checks": ["online", "firmware"],
            },
        )
    assert create.status_code == 202
    iid = create.json()["data"]["id"]
    with TestClient(app) as c:
        get = c.get(
            f"/api/inspections/{iid}", headers=ctx["headers"]
        )
    assert get.status_code == 200


def test_create_inspection_scope_rooms(ctx):
    with TestClient(app) as c:
        resp = c.post(
            "/api/inspections",
            headers=ctx["headers"],
            json={
                "scope": "rooms",
                "roomIds": [1, 2],
                "checks": ["online"],
            },
        )
    assert resp.status_code == 202


def test_create_inspection_invalid_scope(ctx):
    with TestClient(app) as c:
        resp = c.post(
            "/api/inspections",
            headers=ctx["headers"],
            json={"scope": "random", "checks": ["online"]},
        )
    assert resp.status_code == 422


def test_save_and_read_schedule(ctx):
    with TestClient(app) as c:
        put = c.put(
            "/api/schedules/2026-08-31",
            headers=ctx["headers"],
            json={
                "enabled": True,
                "repeatDays": [1, 2, 3, 4, 5],
                "targets": {"lights": [12]},
                "items": [{"time": "19:00", "deviceId": 12, "action": "on"}],
            },
        )
    assert put.status_code == 200
    with TestClient(app) as c:
        get = c.get(
            "/api/schedules/2026-08-31", headers=ctx["headers"]
        )
    assert get.status_code == 200
    body = get.json()["data"]
    assert body["enabled"] is True


def test_read_schedule_returns_null_when_absent(ctx):
    with TestClient(app) as c:
        resp = c.get(
            "/api/schedules/2030-01-01", headers=ctx["headers"]
        )
    assert resp.status_code == 200
    assert resp.json()["data"] is None


def test_create_and_get_sync_job(ctx):
    with TestClient(app) as c:
        create = c.post(
            "/api/device-sync-jobs",
            headers=ctx["headers"],
            json={
                "scope": "all",
                "sources": ["Home Assistant"],
                "options": {},
                "idempotencyKey": "sync-1",
            },
        )
    assert create.status_code == 202
    jid = create.json()["data"]["id"]
    with TestClient(app) as c:
        get = c.get(
            f"/api/device-sync-jobs/{jid}", headers=ctx["headers"]
        )
    assert get.status_code == 200


def test_create_sync_job_idempotent(ctx):
    with TestClient(app) as c:
        first = c.post(
            "/api/device-sync-jobs",
            headers=ctx["headers"],
            json={
                "scope": "all",
                "sources": ["Home Assistant"],
                "idempotencyKey": "idempo-key",
            },
        )
        second = c.post(
            "/api/device-sync-jobs",
            headers=ctx["headers"],
            json={
                "scope": "all",
                "sources": ["Home Assistant"],
                "idempotencyKey": "idempo-key",
            },
        )
    assert first.status_code == 202
    assert second.status_code in (200, 202)
    # 同 key 复用同一 job id
    assert first.json()["data"]["id"] == second.json()["data"]["id"]


def test_sync_household_devices(ctx):
    with TestClient(app) as c:
        resp = c.post(
            f"/api/households/{ctx['household_id']}/devices/sync",
            headers=ctx["headers"],
        )
    assert resp.status_code == 202