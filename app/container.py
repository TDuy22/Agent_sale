import logging
from functools import lru_cache
from pathlib import Path

from app.application.chat_service import ChatService
from app.application.flow_engine import FlowEngine
from app.application.quotation_service import QuotationService
from app.application.response_service import ResponseService
from app.application.slot_service import SlotService
from app.infrastructure.config.flow_loader import load_flow
from app.infrastructure.llm.openai_extractor import OpenAISlotExtractor
from app.infrastructure.llm.rule_based_extractor import RuleBasedSlotExtractor
from app.infrastructure.repositories.in_memory_conversation_repository import (
    InMemoryConversationRepository,
)
from app.infrastructure.repositories.yaml_pricing_repository import YamlPricingRepository
from app.settings import Settings, get_settings

logger = logging.getLogger(__name__)


def build_chat_service(settings: Settings | None = None) -> ChatService:
    """Build application dependencies while keeping adapters replaceable."""

    settings = settings or get_settings()
    pricing_repository = YamlPricingRepository(settings.pricing_config_path)
    slot_service = SlotService(pricing_repository)
    quotation_service = QuotationService(pricing_repository)
    response_service = ResponseService()
    flow = load_flow(settings.flow_config_path)

    if (
        settings.slot_extractor.lower() == "openai"
        and settings.openai_api_key
        and settings.openai_model
    ):
        prompt = Path("app/prompts/slot_extraction.md").read_text(encoding="utf-8")
        extractor = OpenAISlotExtractor(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            prompt=prompt,
        )
    else:
        if settings.slot_extractor.lower() == "openai":
            logger.warning(
                "OpenAI extractor requested without key/model; using rule-based extractor"
            )
        extractor = RuleBasedSlotExtractor()

    engine = FlowEngine(flow, slot_service, quotation_service, response_service)
    return ChatService(InMemoryConversationRepository(), extractor, engine)


@lru_cache
def get_chat_service() -> ChatService:
    return build_chat_service()
