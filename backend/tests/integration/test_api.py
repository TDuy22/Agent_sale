from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.container import Container, get_container
from app.main import app


@pytest.fixture
def client(container: Container) -> Iterator[TestClient]:
    app.dependency_overrides[get_container] = lambda: container
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_full_quote_over_http(client: TestClient) -> None:
    health = client.get("/health")
    session = client.post("/api/v1/sessions")
    session_id = session.json()["session_id"]
    chat = client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "Nhà xây mới, inox cánh kính màu xám 3m."},
    )
    fetched = client.get(f"/api/v1/sessions/{session_id}")

    assert health.json() == {"status": "ok", "extractor": "rule_based"}
    assert session.status_code == 201
    assert session.json()["message_history"][0]["role"] == "assistant"
    assert chat.status_code == 200
    assert chat.json()["quote"]["subtotal"] == 33_600_000
    assert chat.json()["quote"]["material_name"] == "Inox cánh kính"
    assert fetched.json()["status"] == "QUOTED"


def test_chat_can_create_session_when_id_is_omitted(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "Nhà tôi xây mới."})

    assert response.status_code == 200
    assert response.json()["current_section"] == "material"
    assert response.json()["session_id"]


def test_session_history_can_be_restored_with_assets(client: TestClient) -> None:
    session_id = client.post("/api/v1/sessions").json()["session_id"]
    client.post(
        "/api/v1/chat",
        json={"session_id": session_id, "message": "Nhà xây mới, cho anh xem mẫu tủ bếp"},
    )

    restored = client.get(f"/api/v1/sessions/{session_id}").json()

    assert [message["role"] for message in restored["message_history"]] == [
        "assistant",
        "user",
        "assistant",
    ]
    assert restored["message_history"][-1]["assets"][0]["id"] == "kitchen_sample_combined"
    assert restored["missing_slots"] == ["material_code"]


def test_unknown_session_returns_404(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"session_id": "missing", "message": "Xin chào"})

    assert response.status_code == 404


def test_chat_returns_servable_asset_urls(client: TestClient) -> None:
    response = client.post("/api/v1/chat", json={"message": "Cho anh xem mẫu tủ bếp"})
    assets = response.json()["assets"]

    assert [asset["id"] for asset in assets] == ["kitchen_sample_combined"]
    image = client.get(assets[0]["url"])
    assert image.status_code == 200
    assert image.headers["content-type"] == "image/jpeg"
    assert client.get("/api/v1/assets/unknown/image").status_code == 404
