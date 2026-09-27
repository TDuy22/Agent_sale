import logging

from app.application.ports import SlotExtractor
from app.domain.models.conversation import SlotExtractionResult

logger = logging.getLogger(__name__)


class FallbackSlotExtractor:
    """Uses an LLM extractor and degrades to a local one when the provider call fails."""

    def __init__(self, primary: SlotExtractor, fallback: SlotExtractor) -> None:
        self.primary = primary
        self.fallback = fallback
        self.name = primary.name

    def extract(self, message: str) -> SlotExtractionResult:
        try:
            return self.primary.extract(message)
        except Exception:
            # Provider SDKs raise many unrelated error types (network, quota, schema).
            logger.exception("%s failed; using %s", self.primary.name, self.fallback.name)
            return self.fallback.extract(message)
