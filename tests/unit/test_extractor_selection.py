from app.container import build_slot_extractor
from app.infrastructure.llm.gemini_extractor import GeminiSlotExtractor
from app.infrastructure.llm.openai_extractor import OpenAISlotExtractor
from app.infrastructure.llm.rule_based_extractor import RuleBasedSlotExtractor
from app.settings import Settings


def test_uses_rule_based_extractor_without_api_key() -> None:
    settings = Settings(
        slot_extractor="auto",
        openai_api_key=None,
        openai_model="gpt-5.4-mini",
        gemini_api_key=None,
        gemini_model="gemini-3.5-flash-lite",
        _env_file=None,
    )

    assert isinstance(build_slot_extractor(settings), RuleBasedSlotExtractor)


def test_uses_configured_openai_extractor_with_api_key() -> None:
    settings = Settings(
        slot_extractor="openai",
        openai_api_key="test-key",
        openai_model="gpt-5.4-mini",
        _env_file=None,
    )

    extractor = build_slot_extractor(settings)

    assert isinstance(extractor, OpenAISlotExtractor)
    assert extractor._model == settings.openai_model


def test_uses_configured_gemini_extractor_with_api_key() -> None:
    settings = Settings(
        slot_extractor="gemini",
        gemini_api_key="test-key",
        gemini_model="gemini-3.5-flash-lite",
        _env_file=None,
    )

    extractor = build_slot_extractor(settings)

    assert isinstance(extractor, GeminiSlotExtractor)
    assert extractor._model == settings.gemini_model
