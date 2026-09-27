from typing import Any

from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from app.domain.enums import UserIntent
from app.domain.models.conversation import ExtractedSlot, SlotExtractionResult


class GeminiExtractedSlot(BaseModel):
    name: str
    value: str | float | bool | list[str] | None
    confidence: float = Field(ge=0, le=1)


class GeminiExtraction(BaseModel):
    extracted_slots: list[GeminiExtractedSlot]
    corrections: list[str]
    unresolved_references: list[str]
    intents: list[UserIntent]
    confidence: float = Field(ge=0, le=1)


class GeminiSlotExtractor:
    """Gemini structured-output adapter limited to slot and intent extraction."""

    def __init__(self, api_key: str, model: str, prompt: str) -> None:
        if not api_key or not model:
            raise ValueError("GEMINI_API_KEY and GEMINI_MODEL are required")
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=15_000,
                retry_options=types.HttpRetryOptions(
                    attempts=2,
                    initial_delay=1,
                    max_delay=2,
                    jitter=0.2,
                ),
            ),
        )
        self._model = model
        self._prompt = prompt

    def extract(self, message: str) -> SlotExtractionResult:
        response = self._client.models.generate_content(
            model=self._model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=self._prompt,
                response_mime_type="application/json",
                response_schema=GeminiExtraction,
            ),
        )
        parsed: Any = response.parsed
        if parsed is None and response.text:
            parsed = GeminiExtraction.model_validate_json(response.text)
        elif parsed is not None and not isinstance(parsed, GeminiExtraction):
            parsed = GeminiExtraction.model_validate(parsed)
        if parsed is None:
            return SlotExtractionResult(unresolved_references=[message], confidence=0)
        return SlotExtractionResult(
            extracted_slots=[ExtractedSlot(**item.model_dump()) for item in parsed.extracted_slots],
            corrections=parsed.corrections,
            unresolved_references=parsed.unresolved_references,
            intents=parsed.intents,
            confidence=parsed.confidence,
        )
