from fastapi.testclient import TestClient


def test_list_households(client: TestClient) -> None:
    response = client.get("/api/households")

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": 1,
            "name": "鏄熸渤鍏瘬",
            "address": "涓婃捣甯傛郸涓滄柊鍖?,
            "timezone": "Asia/Shanghai",
            "created_by": 1,
            "created_at": response.json()[0]["created_at"],
            "updated_at": response.json()[0]["updated_at"],
            "role": "admin",
            "member_count": 1,
        }
    ]


def test_create_household(client: TestClient) -> None:
    response = client.post("/api/households", json={"name": "湖畔之家", "address": "杭州", "timezone": "Asia/Shanghai"})

    assert response.status_code == 201
    assert response.json()["name"] == "湖畔之家"


def test_read_household(client: TestClient) -> None:
    response = client.get("/api/households/1")

    assert response.status_code == 200
    assert response.json()["name"] == "星河公寓"


def test_admin_update_household(client: TestClient) -> None:
    response = client.patch("/api/households/1", json={"name": "星河公寓 Pro"})

    assert response.status_code == 200
    assert response.json()["name"] == "星河公寓 Pro"


def test_member_cannot_update_household(client: TestClient) -> None:
    client.post("/api/households/1/members", json={"email": "member@example.com", "role": "member"})
    response = client.patch("/api/households/1", headers={"X-User-Id": "2"}, json={"name": "普通成员修改"})

    assert response.status_code == 403


def test_non_member_cannot_read_household(client: TestClient) -> None:
    response = client.get("/api/households/1", headers={"X-User-Id": "3"})

    assert response.status_code == 403


def test_invalid_timezone(client: TestClient) -> None:
    response = client.patch("/api/households/1", json={"timezone": "Mars/Shanghai"})

    assert response.status_code == 422
