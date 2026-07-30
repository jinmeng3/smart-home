from fastapi.testclient import TestClient


def add_member(client: TestClient, role: str = "member") -> dict:
    response = client.post("/api/households/1/members", json={"email": "member@example.com", "role": role})
    assert response.status_code == 201
    return response.json()


def test_admin_add_member(client: TestClient) -> None:
    member = add_member(client)

    assert member["email"] == "member@example.com"
    assert member["role"] == "member"


def test_duplicate_member_returns_409(client: TestClient) -> None:
    add_member(client)
    response = client.post("/api/households/1/members", json={"email": "member@example.com", "role": "member"})

    assert response.status_code == 409


def test_member_cannot_add_member(client: TestClient) -> None:
    add_member(client)
    response = client.post(
        "/api/households/1/members",
        headers={"X-User-Id": "2"},
        json={"email": "outsider@example.com", "role": "member"},
    )

    assert response.status_code == 403


def test_admin_update_member_role(client: TestClient) -> None:
    member = add_member(client)
    response = client.patch(f"/api/households/1/members/{member['membership_id']}", json={"role": "admin"})

    assert response.status_code == 200
    assert response.json()["role"] == "admin"


def test_cannot_update_own_role(client: TestClient) -> None:
    response = client.patch("/api/households/1/members/1", json={"role": "member"})

    assert response.status_code == 400


def test_cannot_downgrade_last_admin(client: TestClient) -> None:
    response = client.patch("/api/households/1/members/1", headers={"X-User-Id": "2"}, json={"role": "member"})

    assert response.status_code in {400, 403}


def test_cannot_delete_self(client: TestClient) -> None:
    response = client.delete("/api/households/1/members/1")

    assert response.status_code == 400


def test_delete_member(client: TestClient) -> None:
    member = add_member(client)
    response = client.delete(f"/api/households/1/members/{member['membership_id']}")

    assert response.status_code == 204
