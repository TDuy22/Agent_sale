from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.schemas.chat import ChatRequest, ChatResponse
from app.application.chat_service import ChatService
from app.container import get_chat_service

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
def chat(
    payload: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatResponse:
    result = service.chat(payload.message, payload.session_id)
    return ChatResponse.model_validate(result.model_dump())
