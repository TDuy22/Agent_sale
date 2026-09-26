from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.schemas.session import SessionResponse
from app.application.chat_service import ChatService
from app.container import get_chat_service

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=SessionResponse, status_code=201)
def create_session(
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> SessionResponse:
    return SessionResponse.model_validate(service.create_session().model_dump())


@router.get("/sessions/{session_id}", response_model=SessionResponse)
def get_session(
    session_id: str,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> SessionResponse:
    return SessionResponse.model_validate(service.get_session(session_id).model_dump())
