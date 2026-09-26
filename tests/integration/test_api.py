from starlette.testclient import TestClient

from app.application.chat_service import ChatService
from app.container import get_chat_service
from app.main import app


def test_api_works_without_openai_key(service: ChatService) -> None:
    app.dependency_overrides[get_chat_service] = lambda: service
    client = TestClient(app)
    try:
        health = client.get("/health")
        session = client.post("/api/v1/sessions")
        session_id = session.json()["session_id"]
        chat = client.post(
            "/api/v1/chat",
            json={
                "session_id": session_id,
                "message": "Nhà xây mới, inox cánh kính 3m.",
            },
        )
        fetched = client.get(f"/api/v1/sessions/{session_id}")
    finally:
        app.dependency_overrides.clear()

    assert health.status_code == 200
    assert session.status_code == 201
    assert chat.status_code == 200
    assert chat.json()["quote"]["subtotal"] == 33_600_000
    assert fetched.status_code == 200
    assert fetched.json()["status"] == "QUOTED"


def test_chat_can_create_session_when_id_is_omitted(service: ChatService) -> None:
    app.dependency_overrides[get_chat_service] = lambda: service
    client = TestClient(app)
    try:
        response = client.post("/api/v1/chat", json={"message": "Nhà tôi xây mới."})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["current_section"] == "material"
    assert response.json()["session_id"]
