from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.domain.enums import ConversationStatus, UserIntent
from app.domain.models.quote import Quote


def utc_now() -> datetime:
    return datetime.now(UTC)


class SlotValue(BaseModel):
    value: Any
    normalized_value: Any
    source_message: str
    confidence: float = Field(ge=0, le=1)
    updated_at: datetime = Field(default_factory=utc_now)


class ExtractedSlot(BaseModel):
    name: str
    value: Any
    confidence: float = Field(default=1.0, ge=0, le=1)


class SlotExtractionResult(BaseModel):
    extracted_slots: list[ExtractedSlot] = Field(default_factory=list)
    corrections: list[str] = Field(default_factory=list)
    unresolved_references: list[str] = Field(default_factory=list)
    intents: list[UserIntent] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0, le=1)


class SectionAttempts(BaseModel):
    turn_count: int = 0
    failed_attempt_count: int = 0


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str
    asset_ids: list[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=utc_now)


class ConversationState(BaseModel):
    session_id: str
    current_section: str
    status: ConversationStatus = ConversationStatus.COLLECTING
    slots: dict[str, SlotValue] = Field(default_factory=dict)
    attempts_by_section: dict[str, SectionAttempts] = Field(default_factory=dict)
    last_asked_fields: list[str] = Field(default_factory=list)
    last_asked_section: str | None = None
    message_history: list[ConversationMessage] = Field(default_factory=list)
    completed_sections: list[str] = Field(default_factory=list)
    last_intents: list[UserIntent] = Field(default_factory=list)
    quote_version: int = 0
    quote: Quote | None = None
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
