from app.application.image_asset_skill import ImageAssetSkill
from app.domain.enums import UserIntent
from app.domain.models.conversation import ConversationState, SlotValue
from app.infrastructure.keyword_asset_matcher import KeywordAssetMatcher
from app.infrastructure.repositories.yaml_assets import YamlAssetRepository
from app.settings import Settings


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


def _skill() -> ImageAssetSkill:
    repository = YamlAssetRepository(Settings(_env_file=None).asset_config_path)
    return ImageAssetSkill(repository, KeywordAssetMatcher())


def test_image_asset_skill_matches_sample_intent() -> None:
    result = _skill().select_assets(
        _state(),
        "Cho anh xem mẫu",
        [UserIntent.SHOW_SAMPLE],
        [],
    )

    assert [asset.asset_id for asset in result] == ["kitchen_sample_combined"]
    assert result[0].file.is_file()


def test_image_asset_skill_honors_flow_suggestion() -> None:
    result = _skill().select_assets(
        _state(),
        "Anh chọn màu xám",
        [],
        ["color_sample_combined"],
    )

    assert [asset.asset_id for asset in result] == ["color_sample_combined"]
