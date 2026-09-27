from google import genai
from google.genai import types

from app.domain.models.conversation import SlotExtractionResult
from app.infrastructure.extractors.schema import LLMExtraction, unparsed


class GeminiSlotExtractor:
    """Gemini structured-output adapter limited to slot and intent extraction."""

    def __init__(self, api_key: str, model: str, prompt: str) -> None:
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(
                timeout=15_000,
                retry_options=types.HttpRetryOptions(
                    attempts=2, initial_delay=1, max_delay=2, jitter=0.2
                ),
            ),
        )
        self._model = model
        self._prompt = prompt
        self.name = f"gemini:{model}"

    def extract(self, message: str) -> SlotExtractionResult:
        response = self._client.models.generate_content(
            model=self._model,
            contents=message,
            config=types.GenerateContentConfig(
                system_instruction=self._prompt,
                response_mime_type="application/json",
                response_schema=LLMExtraction,
            ),
        )
        parsed = response.parsed
        if isinstance(parsed, LLMExtraction):
            return parsed.to_domain()
        if parsed is not None:
            return LLMExtraction.model_validate(parsed).to_domain()
        if response.text:
            return LLMExtraction.model_validate_json(response.text).to_domain()
        return unparsed(message)
