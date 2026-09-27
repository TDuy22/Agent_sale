from app.application.ports import AssetMatcher, AssetRepository
from app.domain.enums import UserIntent
from app.domain.models.asset import AssetQuery
from app.domain.models.conversation import ConversationState


class ImageAssetSkill:
    """Selects asset IDs from conversation context without exposing file choice to an LLM."""

    def __init__(self, repository: AssetRepository, matcher: AssetMatcher) -> None:
        self._repository = repository
        self._matcher = matcher

    def select_assets(
        self,
        state: ConversationState,
        message: str,
        intents: list[UserIntent],
        suggested_asset_ids: list[str],
    ) -> list[str]:
        material = state.slots.get("material_code")
        query = AssetQuery(
            message=message,
            material_code=(str(material.normalized_value) if material else None),
            intents=intents,
            suggested_asset_ids=suggested_asset_ids,
        )
        return self._matcher.match(query, self._repository.list_assets())
