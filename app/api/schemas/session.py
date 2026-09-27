from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import ConversationStatus, UserIntent
from app.domain.models.conversation import ConversationMessage, SectionAttempts, SlotValue
from app.domain.models.quote import Quote


class SessionResponse(BaseModel):
    session_id: str
    current_section: str
    status: ConversationStatus
    slots: dict[str, SlotValue]
    attempts_by_section: dict[str, SectionAttempts]
    last_asked_fields: list[str]
    message_history: list[ConversationMessage]
    completed_sections: list[str]
    last_intents: list[UserIntent]
    quote_version: int
    quote: Quote | None
    created_at: datetime
    updated_at: datetime
