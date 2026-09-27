import pytest

from app.container import build_slot_extractor
from app.domain.models.conversation import SlotExtractionResult
from app.infrastructure.extractors.fallback import FallbackSlotExtractor
from app.infrastructure.extractors.gemini import GeminiSlotExtractor
from app.infrastructure.extractors.openai import OpenAISlotExtractor
from app.infrastructure.extractors.rule_based import RuleBasedSlotExtractor
from app.infrastructure.repositories.yaml_pricing import YamlPricingRepository
from app.settings import Settings


def _build(**overrides: object):
    settings = Settings(_env_file=None, **overrides)
    catalog = YamlPricingRepository(settings.pricing_config_path).get_catalog()
    return build_slot_extractor(settings, catalog)


def test_uses_rule_based_extractor_without_api_key() -> None:
    extractor = _build(slot_extractor="auto", openai_model="m", gemini_model="m")

    assert isinstance(extractor, RuleBasedSlotExtractor)


@pytest.mark.parametrize(
    ("provider", "extractor_cls"),
    [("openai", OpenAISlotExtractor), ("gemini", GeminiSlotExtractor)],
)
def test_wraps_configured_provider_with_local_fallback(provider: str, extractor_cls: type) -> None:
    extractor = _build(
        slot_extractor=provider,
        **{f"{provider}_api_key": "test-key", f"{provider}_model": "test-model"},
    )

    assert isinstance(extractor, FallbackSlotExtractor)
    assert isinstance(extractor.primary, extractor_cls)
    assert extractor.name == f"{provider}:test-model"


def test_prompt_lists_catalog_materials() -> None:
    extractor = _build(slot_extractor="gemini", gemini_api_key="k", gemini_model="m")

    assert "- inox_glass: Inox cánh kính" in extractor.primary._prompt
    assert "{materials}" not in extractor.primary._prompt


class _BrokenExtractor:
    name = "broken"

    def extract(self, message: str) -> SlotExtractionResult:
        raise TimeoutError("provider timed out")


def test_fallback_uses_local_extractor_when_provider_fails() -> None:
    extractor = FallbackSlotExtractor(_BrokenExtractor(), RuleBasedSlotExtractor())

    result = extractor.extract("Nhà anh xây mới")

    assert result.extracted_slots[0].value == "new_build"
