from typing import Any

from openai import OpenAI
from pydantic import BaseModel, Field

from app.domain.enums import UserIntent
from app.domain.models.conversation import ExtractedSlot, SlotExtractionResult


class OpenAIExtractedSlot(BaseModel):
    name: str
    value: str | float | bool | list[str] | None
    confidence: float = Field(ge=0, le=1)


class OpenAIExtraction(BaseModel):
    extracted_slots: list[OpenAIExtractedSlot]
    corrections: list[str]
    unresolved_references: list[str]
    intents: list[UserIntent]
    confidence: float = Field(ge=0, le=1)


class OpenAISlotExtractor:
    """Optional structured-output extractor. It never controls flow or pricing."""

    def __init__(self, api_key: str, model: str, prompt: str) -> None:
        if not api_key or not model:
            raise ValueError("OPENAI_API_KEY and OPENAI_MODEL are required")
        self._client = OpenAI(api_key=api_key)
        self._model = model
        self._prompt = prompt

    def extract(self, message: str) -> SlotExtractionResult:
        response = self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": self._prompt},
                {"role": "user", "content": message},
            ],
            text_format=OpenAIExtraction,
        )
        parsed: Any = response.output_parsed
        if parsed is None:
            return SlotExtractionResult(unresolved_references=[message], confidence=0)
        return SlotExtractionResult(
            extracted_slots=[ExtractedSlot(**item.model_dump()) for item in parsed.extracted_slots],
            corrections=parsed.corrections,
            unresolved_references=parsed.unresolved_references,
            intents=parsed.intents,
            confidence=parsed.confidence,
        )
