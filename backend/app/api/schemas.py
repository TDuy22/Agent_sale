from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from app.domain.enums import ConversationStatus
from app.domain.models.conversation import SectionAttempts, SlotValue
from app.domain.models.quote import Quote


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class AssetOut(BaseModel):
    id: str
    description: str
    url: str = Field(description="Image path relative to the API root")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: ConversationStatus
    current_section: str
    completed_sections: list[str]
    collected_slots: dict[str, SlotValue]
    missing_slots: list[str]
    attempts: dict[str, SectionAttempts]
    quote: Quote | None
    assets: list[AssetOut]


class MessageOut(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    assets: list[AssetOut]
    created_at: datetime


class SessionResponse(BaseModel):
    session_id: str
    status: ConversationStatus
    current_section: str
    completed_sections: list[str]
    slots: dict[str, SlotValue]
    missing_slots: list[str]
    attempts_by_section: dict[str, SectionAttempts]
    message_history: list[MessageOut]
    quote: Quote | None
    created_at: datetime
    updated_at: datetime


class HealthResponse(BaseModel):
    status: str
    extractor: str
