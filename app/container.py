import logging
from functools import lru_cache
from pathlib import Path

from app.application.chat_service import ChatService
from app.application.flow_engine import FlowEngine
from app.application.image_asset_skill import ImageAssetSkill
from app.application.ports import SlotExtractor
from app.application.quotation_service import QuotationService
from app.application.response_service import ResponseService
from app.application.slot_service import SlotService
from app.infrastructure.assets.keyword_asset_matcher import KeywordAssetMatcher
from app.infrastructure.config.flow_loader import load_flow
from app.infrastructure.llm.gemini_extractor import GeminiSlotExtractor
from app.infrastructure.llm.openai_extractor import OpenAISlotExtractor
from app.infrastructure.llm.rule_based_extractor import RuleBasedSlotExtractor
from app.infrastructure.repositories.asset_repository import YamlAssetRepository
from app.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from app.infrastructure.repositories.yaml_pricing_repository import YamlPricingRepository
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def build_slot_extractor(settings: Settings) -> SlotExtractor:
    """Select the configured LLM adapter, with a fully local final fallback."""

    mode = settings.slot_extractor.strip().lower()
    if mode == "rule_based":
        return RuleBasedSlotExtractor()

    prompt = Path("app/prompts/slot_extraction.md").read_text(encoding="utf-8")
    if mode == "gemini":
        if settings.gemini_api_key and settings.gemini_model:
            return GeminiSlotExtractor(
                api_key=settings.gemini_api_key,
                model=settings.gemini_model,
                prompt=prompt,
            )
        logger.warning("Gemini config is incomplete; using rule-based extractor")
        return RuleBasedSlotExtractor()

    if mode == "openai":
        if settings.openai_api_key and settings.openai_model:
            return OpenAISlotExtractor(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                prompt=prompt,
            )
        logger.warning("OpenAI config is incomplete; using rule-based extractor")
        return RuleBasedSlotExtractor()

    if mode != "auto":
        logger.warning("Unknown SLOT_EXTRACTOR=%s; using rule-based extractor", mode)
        return RuleBasedSlotExtractor()

    if settings.openai_api_key and settings.openai_model:
        return OpenAISlotExtractor(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            prompt=prompt,
        )
    if settings.gemini_api_key and settings.gemini_model:
        return GeminiSlotExtractor(
            api_key=settings.gemini_api_key,
            model=settings.gemini_model,
            prompt=prompt,
        )
    return RuleBasedSlotExtractor()


def build_chat_service(settings: Settings | None = None) -> ChatService:
    """Build application dependencies while keeping adapters replaceable."""

    settings = settings or get_settings()
    pricing_repository = YamlPricingRepository(settings.pricing_config_path)
    slot_service = SlotService(pricing_repository)
    quotation_service = QuotationService(pricing_repository)
    response_service = ResponseService()
    flow = load_flow(settings.flow_config_path)
    asset_repository = YamlAssetRepository(settings.asset_config_path)
    asset_skill = ImageAssetSkill(asset_repository, KeywordAssetMatcher())

    extractor = build_slot_extractor(settings)

    engine = FlowEngine(
        flow,
        slot_service,
        quotation_service,
        response_service,
        asset_skill,
    )
    return ChatService(InMemoryConversationRepository(), extractor, engine)


@lru_cache
def get_chat_service() -> ChatService:
    return build_chat_service()


@lru_cache
def get_asset_repository() -> YamlAssetRepository:
    return YamlAssetRepository(get_settings().asset_config_path)
