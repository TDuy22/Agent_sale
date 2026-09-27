from pathlib import Path
from typing import Any

import yaml

from app.domain.exceptions import ConfigurationError


def read_yaml(path: Path, label: str) -> dict[str, Any]:
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        raise ConfigurationError(f"Cannot load {label} configuration: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigurationError(f"{label} configuration must be a YAML mapping: {path}")
    return payload
