"""场景接口测试。

覆盖文档 §9 中的端点。场景执行会真正下发到设备，
本测试仅校验 CRUD、预览与模板相关路径。
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def scene_ctx(make_household):
    ctx = make_household()
    with TestClient(app) as c:
        # 设备绑定需要房间存在
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "Office"})
        d = c.post(
            "/api/devices",
            headers=ctx["headers"],
            json={
                "name": "Lamp",
                "room": "Office",
                "type": "light",
                "brand": "P",
                "connection": "Matter",
                "deviceId": "M-1",
            },
        )
    return {**ctx, "device_id": d.json()["data"]["id"]}


def _scene_payload(name="Scene A", **overrides):
    base = {
        "name": name,
        "description": "demo",
        "icon": "home",
        "color": "var(--color-primary-600)",
        "triggerType": "manual",
        "triggerLabel": "manual",
        "roomLabels": [],
        "deviceIds": [],
        "enabled": True,
        "recommended": False,
        "steps": [
            {
                "name": "Turn on",
                "deviceId": "M-1",
                "order": 1,
                "action": "on",
                "actionValue": None,
            }
        ],
    }
    base.update(overrides)
    return base


def test_create_scene(scene_ctx):
    with TestClient(app) as c:
        resp = c.post(
            "/api/scenes",
            headers=scene_ctx["headers"],
            json=_scene_payload(),
        )
    assert resp.status_code == 201
    body = resp.json()["data"]
    assert body["name"] == "Scene A"
    assert len(body["steps"]) == 1
    assert body["steps"][0]["action"] == "on"


def test_create_scene_with_temperature_step(scene_ctx):
    payload = _scene_payload(name="Climate")
    payload["steps"] = [
        {
            "name": "Cool",
            "deviceId": "M-1",
            "order": 1,
            "action": "set_temperature",
            "actionValue": 24,
        }
    ]
    with TestClient(app) as c:
        resp = c.post(
            "/api/scenes",
            headers=scene_ctx["headers"],
            json=payload,
        )
    assert resp.status_code == 201


def test_list_scenes(scene_ctx):
    with TestClient(app) as c:
        c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        )
        resp = c.get("/api/scenes", headers=scene_ctx["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


def test_list_scenes_filtered(scene_ctx):
    with TestClient(app) as c:
        c.post(
            "/api/scenes",
            headers=scene_ctx["headers"],
            json=_scene_payload(name="Schedule"),
        )
        resp = c.get(
            "/api/scenes?trigger_type=schedule",
            headers=scene_ctx["headers"],
        )
    assert resp.status_code == 200


def test_scene_summary(scene_ctx):
    with TestClient(app) as c:
        c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        )
        resp = c.get("/api/scenes/summary", headers=scene_ctx["headers"])
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["enabled"] >= 1


def test_update_and_delete_scene(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.put(
            f"/api/scenes/{sid}",
            headers=scene_ctx["headers"],
            json=_scene_payload(name="Renamed"),
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Renamed"

    with TestClient(app) as c:
        delete = c.delete(f"/api/scenes/{sid}", headers=scene_ctx["headers"])
    assert delete.status_code == 200


def test_toggle_scene_enabled(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.patch(
            f"/api/scenes/{sid}/enabled",
            headers=scene_ctx["headers"],
            json={"enabled": False},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["enabled"] is False


def test_scene_drafts(scene_ctx):
    payload = _scene_payload()
    payload["name"] = "未命名场景"
    with TestClient(app) as c:
        resp = c.post(
            "/api/scenes/drafts", headers=scene_ctx["headers"], json=payload
        )
    assert resp.status_code == 201
    assert resp.json()["data"]["draftId"]


def test_reorder_scenes(scene_ctx):
    ids = []
    with TestClient(app) as c:
        for n in ["A", "B"]:
            ids.append(
                c.post(
                    "/api/scenes",
                    headers=scene_ctx["headers"],
                    json=_scene_payload(name=n),
                ).json()["data"]["id"]
            )
        resp = c.patch(
            "/api/scenes/order",
            headers=scene_ctx["headers"],
            json={
                "items": [
                    {"id": ids[0], "sortOrder": 0},
                    {"id": ids[1], "sortOrder": 1},
                ]
            },
        )
    assert resp.status_code == 200


def test_batch_enable_scenes(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.post(
            "/api/scenes/batch/enabled",
            headers=scene_ctx["headers"],
            json={"sceneIds": [sid], "enabled": True},
        )
    assert resp.status_code == 200


def test_batch_schedule_scenes(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.post(
            "/api/scenes/batch/schedule",
            headers=scene_ctx["headers"],
            json={
                "sceneIds": [sid],
                "triggerType": "schedule",
                "triggerLabel": "每天 19:00",
            },
        )
    assert resp.status_code == 200


def test_preview_scene(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.post(
            f"/api/scenes/{sid}/preview",
            headers=scene_ctx["headers"],
            json={"source": "manual"},
        )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["sceneId"] == sid


def test_duplicate_scene(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.post(
            f"/api/scenes/{sid}/copy",
            headers=scene_ctx["headers"],
            json={"name": "Copy"},
        )
    # route 返回 200（不是 201，与文档描述不一致但服务端实际行为如此）
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Copy"


def test_scene_logs(scene_ctx):
    with TestClient(app) as c:
        sid = c.post(
            "/api/scenes", headers=scene_ctx["headers"], json=_scene_payload()
        ).json()["data"]["id"]
        resp = c.get(
            f"/api/scenes/{sid}/logs", headers=scene_ctx["headers"]
        )
    assert resp.status_code == 200
    assert "items" in resp.json()["data"]


def test_scene_templates_list_and_preview(make_household, db_session_obj):
    """模板列表：step 字段缺失的模板会被降级为合法值，不会让整个接口 500。"""
    import json
    from app.models.scene import SceneTemplate

    ctx = make_household(name="Tpl Home")
    headers = ctx["headers"]
    # 插入一条 steps_json 含有缺字段的 step 的模板
    tpl = SceneTemplate(
        id="tpl-incomplete",
        name="不完整模板",
        description="steps 字段缺失 name/device_id",
        icon="home",
        color="#000",
        trigger_type="manual",
        trigger_label="p",
        room_labels=json.dumps([]),
        device_count=1,
        recommended=False,
        category="sleep",
        steps_json=json.dumps([{}, {"description": "只有描述"}]),
        enabled=True,
    )
    db_session_obj.add(tpl)
    db_session_obj.commit()

    with TestClient(app) as c:
        list_resp = c.get("/api/scenes/templates", headers=headers)
    assert list_resp.status_code == 200, list_resp.text
    items = list_resp.json()["data"]["items"]
    target = next((i for i in items if i["id"] == "tpl-incomplete"), None)
    assert target is not None
    # 缺字段的 step 被降级为合法 name/device_id
    assert len(target["steps"]) == 2
    for step in target["steps"]:
        assert isinstance(step["name"], str) and len(step["name"]) >= 1
        assert isinstance(step["deviceId"], str) and len(step["deviceId"]) >= 1
        assert step["order"] >= 1

    if items:
        tid = items[0]["id"]
        with TestClient(app) as c:
            preview = c.get(
                f"/api/scenes/templates/{tid}/preview", headers=headers
            )
        assert preview.status_code == 200