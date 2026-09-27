from types import SimpleNamespace

from app.domain.enums import UserIntent
from app.infrastructure.llm.gemini_extractor import (
    GeminiExtractedSlot,
    GeminiExtraction,
    GeminiSlotExtractor,
)


class FakeModels:
    def __init__(self, parsed: GeminiExtraction) -> None:
        self._parsed = parsed
        self.request: dict[str, object] = {}

    def generate_content(self, **kwargs: object) -> SimpleNamespace:
        self.request = kwargs
        return SimpleNamespace(parsed=self._parsed, text=None)


def test_maps_gemini_structured_output_to_domain_result() -> None:
    parsed = GeminiExtraction(
        extracted_slots=[
            GeminiExtractedSlot(name="material_code", value="inox_glass", confidence=0.98)
        ],
        corrections=[],
        unresolved_references=[],
        intents=[UserIntent.SHOW_SAMPLE],
        confidence=0.98,
    )
    fake_models = FakeModels(parsed)
    extractor = GeminiSlotExtractor("test-key", "test-model", "system prompt")
    extractor._client = SimpleNamespace(models=fake_models)

    result = extractor.extract("Cho anh xem mẫu inox cánh kính")

    assert result.extracted_slots[0].value == "inox_glass"
    assert result.intents == [UserIntent.SHOW_SAMPLE]
    assert fake_models.request["model"] == "test-model"
    assert fake_models.request["contents"] == "Cho anh xem mẫu inox cánh kính"
