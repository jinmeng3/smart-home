from fastapi.testclient import TestClient

from app.main import app


def unwrap(response, expected_status=200):
    assert response.status_code == expected_status, response.text
    body = response.json()
    assert body["code"] == 0, body
    return body["data"]


def register(client: TestClient, email: str) -> dict[str, str]:
    data = unwrap(
        client.post(
            "/api/auth/register",
            json={
                "username": email.split("@")[0],
                "email": email,
                "password": "password123",
            },
        )
    )
    return {"Authorization": f"Bearer {data['accessToken']}"}


def create_household_and_room(client: TestClient, headers: dict[str, str], name: str):
    unwrap(
        client.post(
            "/api/households",
            headers=headers,
            json={"name": name, "timezone": "Asia/Shanghai"},
        ),
        201,
    )
    return unwrap(
        client.post(
            "/api/rooms",
            headers=headers,
            json={"name": "客厅", "floor": "1F", "roomType": "living"},
        ),
        201,
    )


def test_devices_and_scenes_are_isolated_by_household():
    with TestClient(app) as client:
        owner_headers = register(client, "owner@example.com")
        owner_room = create_household_and_room(client, owner_headers, "Owner Home")
        device = unwrap(
            client.post(
                "/api/devices",
                headers=owner_headers,
                json={
                    "name": "主灯",
                    "room": "客厅",
                    "type": "light",
                    "brand": "Demo",
                    "connection": "Matter",
                },
            ),
            201,
        )
        scene = unwrap(
            client.post(
                "/api/scenes",
                headers=owner_headers,
                json={"name": "回家模式", "roomLabels": ["客厅"], "steps": []},
            ),
            201,
        )
        room_scenes = unwrap(
            client.get(
                f"/api/rooms/{owner_room['id']}/scenes", headers=owner_headers
            )
        )
        assert [item["id"] for item in room_scenes["items"]] == [scene["id"]]

        other_headers = register(client, "other@example.com")
        create_household_and_room(client, other_headers, "Other Home")

        assert client.get(
            f"/api/devices/{device['id']}", headers=other_headers
        ).status_code == 404
        assert unwrap(client.get("/api/devices", headers=other_headers))["total"] == 0
        assert unwrap(client.get("/api/scenes", headers=other_headers))["total"] == 0
        assert client.delete(
            f"/api/scenes/{scene['id']}", headers=other_headers
        ).status_code == 404


def test_legacy_create_routes_remain_compatible():
    with TestClient(app) as client:
        headers = register(client, "legacy@example.com")
        unwrap(
            client.post(
                "/api/households",
                headers=headers,
                json={"name": "Legacy Home", "timezone": "Asia/Shanghai"},
            ),
            201,
        )
        unwrap(
            client.post(
                "/api/rooms/add",
                headers=headers,
                json={"name": "客厅", "roomType": "living"},
            ),
            201,
        )
        unwrap(
            client.post(
                "/api/devices/add",
                headers=headers,
                json={
                    "name": "旧客户端设备",
                    "room": "客厅",
                    "type": "light",
                    "brand": "Demo",
                    "connection": "Matter",
                },
            ),
            201,
        )
