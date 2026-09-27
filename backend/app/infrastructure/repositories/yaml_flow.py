from pathlib import Path

from pydantic import ValidationError

from app.domain.exceptions import ConfigurationError
from app.domain.models.flow import FlowDefinition
from app.infrastructure.repositories.yaml_loader import read_yaml


def load_flow(path: Path) -> FlowDefinition:
    """Load and validate the conversation script from YAML."""

    try:
        return FlowDefinition.model_validate(read_yaml(path, "flow"))
    except ValidationError as exc:
        raise ConfigurationError(f"Invalid flow configuration: {exc}") from exc
