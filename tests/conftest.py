import pytest

from app.application.chat_service import ChatService
from app.container import build_chat_service
from app.settings import Settings


@pytest.fixture
def service() -> ChatService:
    settings = Settings(
        slot_extractor="rule_based",
        flow_config_path="config/flow.yaml",
        pricing_config_path="config/pricing.yaml",
        asset_config_path="config/assets.yaml",
        _env_file=None,
    )
    return build_chat_service(settings)
