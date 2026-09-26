from pydantic import BaseModel, Field

from app.domain.models.conversation import SectionAttempts, SlotValue
from app.domain.models.quote import Quote


class ChatRequest(BaseModel):
    session_id: str | None = None
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    status: str
    current_section: str
    completed_sections: list[str]
    collected_slots: dict[str, SlotValue]
    missing_slots: list[str]
    attempts: dict[str, SectionAttempts]
    quote: Quote | None
    asset_ids: list[str]
