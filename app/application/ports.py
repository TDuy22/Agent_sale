from typing import Protocol

from app.domain.models.asset import Asset
from app.domain.models.conversation import ConversationState, SlotExtractionResult
from app.domain.models.pricing import PricingCatalog


class SlotExtractor(Protocol):
    def extract(self, message: str) -> SlotExtractionResult: ...


class ConversationRepository(Protocol):
    def create(self, state: ConversationState) -> ConversationState: ...

    def get(self, session_id: str) -> ConversationState | None: ...

    def save(self, state: ConversationState) -> ConversationState: ...


class PricingRepository(Protocol):
    def get_catalog(self) -> PricingCatalog: ...


class AssetRepository(Protocol):
    def get(self, asset_id: str) -> Asset | None: ...

    def list_ids(self) -> list[str]: ...
