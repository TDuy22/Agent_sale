from pydantic import BaseModel, Field

from app.domain.enums import UserIntent
from app.domain.models.conversation import ExtractedSlot, SlotExtractionResult


class LLMExtractedSlot(BaseModel):
    name: str
    value: str | float | bool | list[str] | None
    confidence: float = Field(ge=0, le=1)


class LLMExtraction(BaseModel):
    """Strict structured-output schema shared by every LLM provider."""

    extracted_slots: list[LLMExtractedSlot]
    corrections: list[str]
    unresolved_references: list[str]
    intents: list[UserIntent]
    confidence: float = Field(ge=0, le=1)

    def to_domain(self) -> SlotExtractionResult:
        return SlotExtractionResult(
            extracted_slots=[ExtractedSlot(**item.model_dump()) for item in self.extracted_slots],
            corrections=self.corrections,
            unresolved_references=self.unresolved_references,
            intents=self.intents,
            confidence=self.confidence,
        )


def unparsed(message: str) -> SlotExtractionResult:
    return SlotExtractionResult(unresolved_references=[message], confidence=0)
