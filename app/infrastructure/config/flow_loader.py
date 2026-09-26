from pathlib import Path

import yaml
from pydantic import ValidationError

from app.domain.exceptions import ConfigurationError
from app.domain.models.flow import FlowDefinition


def load_flow(path: str | Path) -> FlowDefinition:
    """Load and validate a replaceable flow definition from YAML."""

    try:
        payload = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
        return FlowDefinition.model_validate(payload)
    except (OSError, yaml.YAMLError, ValidationError) as exc:
        raise ConfigurationError(f"Cannot load flow configuration: {exc}") from exc
