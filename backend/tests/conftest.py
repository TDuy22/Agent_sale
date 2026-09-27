import pytest

from app.application.chat_service import ChatService
from app.container import Container, build_container
from app.settings import Settings


@pytest.fixture
def container() -> Container:
    return build_container(Settings(slot_extractor="rule_based", _env_file=None))


@pytest.fixture
def service(container: Container) -> ChatService:
    return container.chat_service
