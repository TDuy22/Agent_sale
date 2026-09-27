from openai import OpenAI

from app.domain.models.conversation import SlotExtractionResult
from app.infrastructure.extractors.schema import LLMExtraction, unparsed


class OpenAISlotExtractor:
    """OpenAI structured-output adapter limited to slot and intent extraction."""

    def __init__(self, api_key: str, model: str, prompt: str) -> None:
        self._client = OpenAI(api_key=api_key, timeout=15, max_retries=1)
        self._model = model
        self._prompt = prompt
        self.name = f"openai:{model}"

    def extract(self, message: str) -> SlotExtractionResult:
        response = self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": self._prompt},
                {"role": "user", "content": message},
            ],
            text_format=LLMExtraction,
        )
        parsed = response.output_parsed
        return parsed.to_domain() if parsed is not None else unparsed(message)
