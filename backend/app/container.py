from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.application.chat_service import ChatService
from app.application.flow_engine import FlowEngine
from app.application.image_asset_skill import ImageAssetSkill
from app.application.ports import SlotExtractor
from app.application.quotation_service import QuotationService
from app.application.response_service import ResponseService
from app.application.slot_service import SlotService
from app.domain.models.pricing import PricingCatalog
from app.infrastructure.extractors.fallback import FallbackSlotExtractor
from app.infrastructure.extractors.gemini import GeminiSlotExtractor
from app.infrastructure.extractors.openai import OpenAISlotExtractor
from app.infrastructure.extractors.rule_based import RuleBasedSlotExtractor
from app.infrastructure.keyword_asset_matcher import KeywordAssetMatcher
from app.infrastructure.repositories.in_memory_conversation import (
    InMemoryConversationRepository,
)
from app.infrastructure.repositories.yaml_assets import YamlAssetRepository
from app.infrastructure.repositories.yaml_flow import load_flow
from app.infrastructure.repositories.yaml_pricing import YamlPricingRepository
from app.settings import Settings, get_settings

PROMPT_PATH = Path(__file__).parent / "prompts" / "slot_extraction.md"


@dataclass(frozen=True)
class Container:
    chat_service: ChatService
    asset_repository: YamlAssetRepository


def build_slot_extractor(settings: Settings, catalog: PricingCatalog) -> SlotExtractor:
    """Pick the configured LLM provider; always fall back to the local rule-based extractor.

    `auto` prefers OpenAI, then Gemini. A provider without both key and model is skipped.
    """

    local = RuleBasedSlotExtractor()
    providers = {
        "openai": (settings.openai_api_key, settings.openai_model, OpenAISlotExtractor),
        "gemini": (settings.gemini_api_key, settings.gemini_model, GeminiSlotExtractor),
    }
    candidates = list(providers) if settings.slot_extractor == "auto" else [settings.slot_extractor]
    for name in candidates:
        if name not in providers:
            continue
        api_key, model, extractor_cls = providers[name]
        if api_key and model:
            primary = extractor_cls(api_key=api_key, model=model, prompt=_prompt(catalog))
            return FallbackSlotExtractor(primary, local)
    return local


def _prompt(catalog: PricingCatalog) -> str:
    materials = "\n".join(f"- {code}: {m.name}" for code, m in catalog.materials.items())
    return PROMPT_PATH.read_text(encoding="utf-8").replace("{materials}", materials)


def build_container(settings: Settings | None = None) -> Container:
    settings = settings or get_settings()
    pricing = YamlPricingRepository(settings.pricing_config_path)
    flow = load_flow(settings.flow_config_path)
    assets = YamlAssetRepository(settings.asset_config_path)

    engine = FlowEngine(
        flow,
        SlotService(pricing),
        QuotationService(pricing),
        ResponseService(flow.slot_labels),
        ImageAssetSkill(assets, KeywordAssetMatcher()),
    )
    extractor = build_slot_extractor(settings, pricing.get_catalog())
    chat_service = ChatService(InMemoryConversationRepository(), extractor, engine)
    return Container(chat_service=chat_service, asset_repository=assets)


@lru_cache
def get_container() -> Container:
    return build_container()
