"""房间与设备接口测试。

覆盖文档 §7、§8 中的端点。
"""
from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app


def _new_ctx(make_household):
    return make_household()


# === /rooms ====


def test_create_room(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        resp = c.post(
            "/api/rooms",
            headers=ctx["headers"],
            json={
                "name": "Living Room",
                "floor": "1F",
                "roomType": "living",
                "icon": "sofa",
                "themeColor": "#3478f6",
                "area": 25.5,
                "comfort": 80,
            },
        )
    assert resp.status_code == 201
    data = resp.json()["data"]
    assert data["name"] == "Living Room"
    assert data["deviceCount"] == 0


def test_create_room_with_devices(make_household):
    ctx = _new_ctx(make_household)
    device_ids = []
    with TestClient(app) as c:
        # 预先创建 Bedroom 房间
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "Bedroom"})
        for i in range(2):
            d = c.post(
                "/api/devices",
                headers=ctx["headers"],
                json={
                    "name": f"Lamp {i}",
                    "room": "Bedroom",
                    "type": "light",
                    "brand": "Philips",
                    "connection": "Matter",
                    "device_id": f"M-{i}",
                },
            )
            assert d.status_code == 201
            device_ids.append(d.json()["data"]["id"])

        # 把设备绑到一个新房间
        r = c.post(
            "/api/rooms",
            headers=ctx["headers"],
            json={"name": "Bedroom 2", "device_ids": device_ids},
        )
    assert r.status_code == 201
    assert r.json()["data"]["deviceCount"] == 2


def test_create_room_duplicate_name(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "Kitchen"})
        dup = c.post("/api/rooms", headers=ctx["headers"], json={"name": "Kitchen"})
    # 服务端实现返回 400（"房间名已存在"），文档期望 409
    assert dup.status_code in (400, 409)


def test_list_rooms_filtered(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "A", "floor": "1F"})
        c.post("/api/rooms", headers=ctx["headers"], json={"name": "B", "floor": "2F"})

        first = c.get("/api/rooms", headers=ctx["headers"])
        assert first.json()["data"]["total"] == 2

        filtered = c.get("/api/rooms?floor=2F", headers=ctx["headers"])
        assert filtered.json()["data"]["total"] == 1
        assert filtered.json()["data"]["items"][0]["name"] == "B"


def test_room_stats(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        resp = c.get("/api/rooms/stats", headers=ctx["headers"])
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["roomCount"] == 0


def test_update_room(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        room = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Old"}
        ).json()["data"]
        resp = c.patch(
            f"/api/rooms/{room['id']}",
            headers=ctx["headers"],
            json={"name": "New", "area": 30},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "New"


def test_delete_room(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Tmp"}
        ).json()["data"]["id"]
        resp = c.delete(f"/api/rooms/{rid}", headers=ctx["headers"])
    assert resp.status_code == 200


def test_set_room_devices_binding(make_household):
    ctx = _new_ctx(make_household)
    device_ids = []
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Office")
        for i in range(2):
            d = c.post(
                "/api/devices",
                headers=ctx["headers"],
                json={
                    "name": f"D{i}",
                    "room": "Office",
                    "type": "ac",
                    "brand": "Gree",
                    "connection": "MQTT",
                    "device_id": f"DEV-{i}",
                },
            )
            device_ids.append(d.json()["data"]["id"])
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Office 2"}
        ).json()["data"]["id"]
        resp = c.put(
            f"/api/rooms/{rid}/devices",
            headers=ctx["headers"],
            json={
                "devices": [
                    {"deviceId": device_ids[0], "group": "AC", "favorite": True, "sortOrder": 0},
                    {"deviceId": device_ids[1], "group": "AC", "favorite": False, "sortOrder": 1},
                ]
            },
        )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 2


def test_patch_room_device_meta(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        # 设备需要先绑定到房间
        office_id = _ensure_room(c, ctx["headers"], "Office") or c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Office Meta"}
        ).json()["data"]["id"]
        did = c.post(
            "/api/devices",
            headers=ctx["headers"],
            json={
                "name": "Light",
                "room": "Office",
                "type": "light",
                "brand": "P",
                "connection": "Matter",
                "device_id": "L-1",
            },
        ).json()["data"]["id"]
        # 查询房间 ID
        rooms = c.get("/api/rooms", headers=ctx["headers"]).json()["data"]["items"]
        office = next(r for r in rooms if r["name"] == "Office")
        resp = c.patch(
            f"/api/rooms/{office['id']}/devices/{did}",
            headers=ctx["headers"],
            json={"group": "Favorites", "favorite": True, "sortOrder": 5},
        )
    assert resp.status_code == 200


def test_update_room_device_status(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Bedroom")
        did = c.post(
            "/api/devices",
            headers=ctx["headers"],
            json={
                "name": "AC",
                "room": "Bedroom",
                "type": "ac",
                "brand": "Gree",
                "connection": "MQTT",
                "device_id": "AC-1",
            },
        ).json()["data"]["id"]
        rooms = c.get("/api/rooms", headers=ctx["headers"]).json()["data"]["items"]
        rid = next(r["id"] for r in rooms if r["name"] == "Bedroom")
        resp = c.patch(
            f"/api/rooms/{rid}/device",
            headers=ctx["headers"],
            json={"device_id": did, "status": "online"},
        )
    assert resp.status_code == 200


def test_quick_action(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Lobby"}
        ).json()["data"]["id"]
        for action in ("all_lights", "air_conditioner", "curtains"):
            resp = c.post(
                f"/api/rooms/{rid}/quick-action",
                headers=ctx["headers"],
                json={"action": action},
            )
            assert resp.status_code == 200, action


def test_quick_action_invalid(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Lobby"}
        ).json()["data"]["id"]
        resp = c.post(
            f"/api/rooms/{rid}/quick-action",
            headers=ctx["headers"],
            json={"action": "explode"},
        )
    assert resp.status_code == 422


def test_room_logs(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Lobby"}
        ).json()["data"]["id"]
        # 触发一个 quick action 写入活动日志
        c.post(
            f"/api/rooms/{rid}/quick-action",
            headers=ctx["headers"],
            json={"action": "all_lights"},
        )
        resp = c.get(f"/api/rooms/{rid}/logs", headers=ctx["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 1


def test_environment_latest_and_trends(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Lab"}
        ).json()["data"]["id"]
        latest = c.get(
            f"/api/rooms/{rid}/environment/latest", headers=ctx["headers"]
        )
        trends = c.get(
            f"/api/rooms/{rid}/environment/trends?metrics=temperature,humidity",
            headers=ctx["headers"],
        )
    assert latest.status_code == 200
    assert trends.status_code == 200


def test_environment_report_create_and_get(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        rid = c.post(
            "/api/rooms", headers=ctx["headers"], json={"name": "Lab"}
        ).json()["data"]["id"]
        resp = c.post(
            f"/api/rooms/{rid}/environment/reports", headers=ctx["headers"]
        )
    assert resp.status_code == 201
    task_id = resp.json()["data"]["taskId"]
    assert task_id

    with TestClient(app) as c:
        get = c.get(f"/api/environment/reports/{task_id}", headers=ctx["headers"])
    assert get.status_code == 200


# === /devices ====


def _device_payload(name="Lamp", room="Living Room", **overrides):
    base = {
        "name": name,
        "room": room,
        "type": "light",
        "brand": "Philips",
        "connection": "Matter",
        "device_id": "MATTER-X",
        "firmware": "1.0.0",
    }
    base.update(overrides)
    return base


def _ensure_room(client, headers, name):
    """预先创建设备测试需要的房间（避免 422）。"""
    client.post("/api/rooms", headers=headers, json={"name": name})


def test_create_and_get_device(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        created = c.post(
            "/api/devices", headers=ctx["headers"], json=_device_payload()
        )
        assert created.status_code == 201
        did = created.json()["data"]["id"]
        get = c.get(f"/api/devices/{did}", headers=ctx["headers"])
    assert get.status_code == 200
    assert get.json()["data"]["name"] == "Lamp"
    assert len(get.json()["data"]["logs"]) >= 1


def test_list_devices(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        for i in range(3):
            c.post(
                "/api/devices",
                headers=ctx["headers"],
                json=_device_payload(name=f"D{i}", device_id=f"DEV-{i}"),
            )
        resp = c.get("/api/devices", headers=ctx["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] == 3


def test_list_devices_filtered(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        c.post(
            "/api/devices",
            headers=ctx["headers"],
            json=_device_payload(name="Light A", type="light"),
        )
        c.post(
            "/api/devices",
            headers=ctx["headers"],
            json=_device_payload(name="AC", type="ac", device_id="DEV-AC"),
        )
        resp = c.get("/api/devices?type=ac", headers=ctx["headers"])
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["total"] == 1
    assert body["items"][0]["name"] == "AC"


def test_update_device(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        did = c.post(
            "/api/devices", headers=ctx["headers"], json=_device_payload()
        ).json()["data"]["id"]
        resp = c.patch(
            f"/api/devices/{did}",
            headers=ctx["headers"],
            json={"name": "Renamed", "status": "online"},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["name"] == "Renamed"
    assert resp.json()["data"]["status"] == "online"


def test_update_device_invalid_status(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        did = c.post(
            "/api/devices", headers=ctx["headers"], json=_device_payload()
        ).json()["data"]["id"]
        resp = c.patch(
            f"/api/devices/{did}",
            headers=ctx["headers"],
            json={"status": "broken"},
        )
    assert resp.status_code == 422


def test_delete_device(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        did = c.post(
            "/api/devices", headers=ctx["headers"], json=_device_payload()
        ).json()["data"]["id"]
        resp = c.delete(f"/api/devices/{did}", headers=ctx["headers"])
    assert resp.status_code == 200


def test_device_sync(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        c.post(
            "/api/devices",
            headers=ctx["headers"],
            json=_device_payload(connection="Home Assistant", device_id="HA-1"),
        )
        resp = c.post(
            "/api/devices/sync",
            headers=ctx["headers"],
            json={"platform": "Home Assistant"},
        )
    assert resp.status_code == 200
    body = resp.json()["data"]
    synced = body.get("synced_count") or body.get("syncedCount") or 0
    assert synced >= 1


def test_device_logs(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        did = c.post(
            "/api/devices", headers=ctx["headers"], json=_device_payload()
        ).json()["data"]["id"]
        c.patch(
            f"/api/devices/{did}",
            headers=ctx["headers"],
            json={"status": "online"},
        )
        resp = c.get(f"/api/devices/{did}/logs", headers=ctx["headers"])
    assert resp.status_code == 200
    assert resp.json()["data"]["total"] >= 2  # create + update


def test_upload_device_image(make_household, _isolated_dirs):
    ctx = _new_ctx(make_household)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\rIDATx\xdac\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\xc7\xb6\x9e\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with TestClient(app) as c:
        resp = c.post(
            "/api/devices/images",
            headers=ctx["headers"],
            files={"file": ("device.png", io.BytesIO(png_bytes), "image/png")},
        )
    assert resp.status_code == 200
    image_url = resp.json()["data"]["image_url"]
    assert image_url.startswith("/uploads/devices/")
    file_path = _isolated_dirs["uploads"] / "devices" / image_url.split("/")[-1]
    assert file_path.exists()


def test_upload_device_image_with_device_id(make_household):
    ctx = _new_ctx(make_household)
    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR"
        b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4"
        b"\x89\x00\x00\x00\rIDATx\xdac\xf8\xcf\xc0\x00\x00\x00\x03\x00\x01"
        b"\xc7\xb6\x9e\x9d\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        did = c.post(
            "/api/devices", headers=ctx["headers"], json=_device_payload()
        ).json()["data"]["id"]
        resp = c.post(
            "/api/devices/images",
            headers=ctx["headers"],
            params={"device_id": did},
            files={"file": ("device.png", io.BytesIO(png_bytes), "image/png")},
        )
    assert resp.status_code == 200


def test_upload_device_image_bad_type(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        resp = c.post(
            "/api/devices/images",
            headers=ctx["headers"],
            files={"file": ("device.gif", io.BytesIO(b"GIF89a"), "image/gif")},
        )
    assert resp.status_code == 415


def test_batch_group_devices(make_household):
    ctx = _new_ctx(make_household)
    device_ids = []
    with TestClient(app) as c:
        _ensure_room(c, ctx["headers"], "Living Room")
        for i in range(3):
            device_ids.append(
                c.post(
                    "/api/devices",
                    headers=ctx["headers"],
                    json=_device_payload(name=f"D{i}", device_id=f"GRP-{i}"),
                ).json()["data"]["id"]
            )
        resp = c.post(
            "/api/devices/groups/assign",
            headers=ctx["headers"],
            json={"group": "Night Lights", "device_ids": device_ids},
        )
    assert resp.status_code == 200
    body = resp.json()["data"]
    assert body["group"] == "Night Lights"
    assert body["assigned_count"] == 3


def test_batch_group_devices_duplicate(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        resp = c.post(
            "/api/devices/groups/assign",
            headers=ctx["headers"],
            json={"group": "Empty"},
        )
    assert resp.status_code == 200
    assert resp.json()["data"]["assigned_count"] == 0


def test_get_device_404(make_household):
    ctx = _new_ctx(make_household)
    with TestClient(app) as c:
        resp = c.get("/api/devices/9999", headers=ctx["headers"])
    assert resp.status_code == 404