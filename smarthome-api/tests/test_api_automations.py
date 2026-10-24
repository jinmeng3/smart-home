"""自动化与 AI 模板生成接口测试。

覆盖文档 §10 中的端点。AI 模板生成依赖真实模型，跳过。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _new_ctx(make_household):
    return make_household()


def _automation_payload(name="Rule A", **overrides):
    base = {
        "name": name,
        "description": "Test rule",
        "enabled": True,
        "triggers": [{"type": "schedule", "config": {"time": "19:00"}}],
        "conditions": [],
        "actions": [
            {
                "type": "device_command",
                "position": 0,
                "config": {"command": "on"},
            }
        ],
        "priority": 2,
        "cooldownSeconds": 0,
        "delaySeconds": 0,
        "note": "",
    }
    base.update(overrides)
    return base


@pytest.fixture()
def automation_ctx(make_household):
    """准备好一个含设备的家庭。"""
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        # 预先创建房间
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "Office"})
        d = c.post(
            "/api/devices",
            headers=ctx["headers"],
            json={
                "name": "Light",
                "room": "Office",
                "type": "light",
                "brand": "P",
                "connection": "Matter",
                "deviceId": "M-1",
            },
        )
        did = d.json()["data"]["id"]
    return {**ctx, "device_id": did}


def test_create_automation(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        resp = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["name"] == "Rule A"


def test_create_automation_requires_device_for_command(automation_ctx):
    payload = _automation_payload()
    # actions[0].device_id 留空，校验应拒绝
    with TestClient(app) as c:
        resp = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        )
    assert resp.status_code == 422


def test_create_automation_unique_positions(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    payload["actions"].append(
        {
            "type": "device_command",
            "position": 0,  # 与第一个冲突
            "device_id": automation_ctx["device_id"],
            "config": {"command": "off"},
        }
    )
    with TestClient(app) as c:
        resp = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        )
    assert resp.status_code == 422


def test_list_automations(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        )
        resp = c.get(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


def test_list_automations_filtered(automation_ctx):
    payload = _automation_payload(name="FilterTarget")
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        )
        resp = c.get(
            f"/api/households/{automation_ctx['household_id']}/automations",
            params={"keyword": "Filter"},
            headers=automation_ctx["headers"],
        )
    assert resp.status_code == 200
    items = resp.json()["data"]["items"]
    assert all("Filter" in i["name"] for i in items)


def test_read_update_delete_automation(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        rule = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]
        rid = rule["id"]

        get = c.get(f"/api/automations/{rid}", headers=automation_ctx["headers"])
        assert get.status_code == 200

        patch = c.patch(
            f"/api/automations/{rid}",
            headers=automation_ctx["headers"],
            json={"name": "Renamed"},
        )
        assert patch.status_code == 200
        assert patch.json()["data"]["name"] == "Renamed"

        delete = c.delete(
            f"/api/automations/{rid}", headers=automation_ctx["headers"]
        )
        assert delete.status_code == 204


def test_toggle_automation_enabled(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        rid = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]["id"]
        resp = c.patch(
            f"/api/automations/{rid}/enabled",
            headers=automation_ctx["headers"],
            json={"enabled": False},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is False


def test_execute_automation(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        rid = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]["id"]
        resp = c.post(
            f"/api/automations/{rid}/execute",
            headers=automation_ctx["headers"],
            headers_=None,
            json={"source": "manual"},
        ) if False else c.post(
            f"/api/automations/{rid}/execute",
            headers=automation_ctx["headers"],
            json={"source": "manual"},
        )
    assert resp.status_code == 202
    assert "executionId" in resp.json()["data"]


def test_get_executions(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        rid = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]["id"]
        c.post(
            f"/api/automations/{rid}/execute",
            headers=automation_ctx["headers"],
            json={"source": "manual"},
        )
        resp = c.get(
            f"/api/automations/{rid}/executions",
            headers=automation_ctx["headers"],
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


def test_batch_enable_automations(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    payload["enabled"] = False  # 初始关闭以便被批量启用
    with TestClient(app) as c:
        rid = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]["id"]
        resp = c.post(
            "/api/automations/batch-enable",
            headers=automation_ctx["headers"],
            json={"ruleIds": [rid], "executeNow": False},
        )
    assert resp.status_code == 200
    body = resp.json()["data"]
    updated = body.get("updated_count") or body.get("updatedCount") or 0
    assert updated >= 1


def test_batch_enable_requires_household(make_user):
    _, headers = make_user(email="nohouse@example.com")
    with TestClient(app) as c:
        resp = c.post(
            "/api/automations/batch-enable",
            headers=headers,
            json={"ruleIds": [1]},
        )
    assert resp.status_code == 403


def test_batch_schedule(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        rid = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]["id"]
        resp = c.put(
            "/api/automations/schedules/batch",
            headers=automation_ctx["headers"],
            json={
                "ruleIds": [rid],
                "timezone": "Asia/Shanghai",
                "time": "19:30",
                "weekdays": [1, 2, 3, 4, 5],
                "frequency": "daily",
                "interval": 1,
            },
        )
    assert resp.status_code == 200


def test_batch_schedule_invalid_time(automation_ctx):
    payload = _automation_payload()
    payload["actions"][0]["device_id"] = automation_ctx["device_id"]
    with TestClient(app) as c:
        rid = c.post(
            f"/api/households/{automation_ctx['household_id']}/automations",
            headers=automation_ctx["headers"],
            json=payload,
        ).json()["data"]["id"]
        resp = c.put(
            "/api/automations/schedules/batch",
            headers=automation_ctx["headers"],
            json={
                "ruleIds": [rid],
                "timezone": "Asia/Shanghai",
                "time": "25:00",
                "weekdays": [1],
            },
        )
    assert resp.status_code == 422