from fastapi.testclient import TestClient


def test_get_account_me(client: TestClient) -> None:
    response = client.get("/api/account/me")

    assert response.status_code == 200
    assert response.json()["email"] == "zhang.xm@company.com"


def test_update_name_and_email(client: TestClient) -> None:
    response = client.patch("/api/account/me", json={"name": "张三", "email": "zhangsan@example.com"})

    assert response.status_code == 200
    assert response.json()["name"] == "张三"
    assert response.json()["email"] == "zhangsan@example.com"


def test_update_duplicate_email(client: TestClient) -> None:
    response = client.patch("/api/account/me", json={"email": "member@example.com"})

    assert response.status_code == 409


def test_upload_avatar(client: TestClient) -> None:
    response = client.post(
        "/api/account/me/avatar",
        files={"avatar": ("avatar.png", b"small-image", "image/png")},
    )

    assert response.status_code == 200
    assert response.json()["avatar_url"].startswith("/uploads/avatars/")


def test_reject_large_avatar(client: TestClient) -> None:
    response = client.post(
        "/api/account/me/avatar",
        files={"avatar": ("avatar.png", b"x" * (2 * 1024 * 1024 + 1), "image/png")},
    )

    assert response.status_code == 413


def test_reject_invalid_avatar_type(client: TestClient) -> None:
    response = client.post(
        "/api/account/me/avatar",
        files={"avatar": ("avatar.txt", b"text", "text/plain")},
    )

    assert response.status_code == 415


def test_delete_avatar(client: TestClient) -> None:
    client.post("/api/account/me/avatar", files={"avatar": ("avatar.webp", b"image", "image/webp")})
    response = client.delete("/api/account/me/avatar")

    assert response.status_code == 200
    assert response.json()["avatar_url"] is None
