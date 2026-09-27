from app.application.image_asset_skill import ImageAssetSkill
from app.domain.enums import UserIntent
from app.domain.models.conversation import ConversationState, SlotValue
from app.infrastructure.assets.keyword_asset_matcher import KeywordAssetMatcher
from app.infrastructure.repositories.asset_repository import YamlAssetRepository


def _state() -> ConversationState:
    return ConversationState(
        session_id="asset-test",
        current_section="material",
        slots={
            "material_code": SlotValue(
                value="inox_glass",
                normalized_value="inox_glass",
                source_message="inox cánh kính",
                confidence=1,
            )
        },
    )


def test_image_asset_skill_matches_sample_intent() -> None:
    repository = YamlAssetRepository("data_image/assets.yaml")
    skill = ImageAssetSkill(repository, KeywordAssetMatcher())

    result = skill.select_assets(
        _state(),
        "Cho anh xem mẫu",
        [UserIntent.SHOW_SAMPLE],
        [],
    )

    assert result == ["kitchen_sample_combined"]
    assert repository.get(result[0]) is not None


def test_image_asset_skill_honors_flow_suggestion() -> None:
    repository = YamlAssetRepository("data_image/assets.yaml")
    skill = ImageAssetSkill(repository, KeywordAssetMatcher())

    result = skill.select_assets(
        _state(),
        "Anh chọn màu xám",
        [],
        ["color_sample_combined"],
    )

    assert result == ["color_sample_combined"]
