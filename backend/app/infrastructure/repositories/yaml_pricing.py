from pathlib import Path

from pydantic import ValidationError

from app.domain.exceptions import ConfigurationError
from app.domain.models.pricing import PricingCatalog
from app.infrastructure.repositories.yaml_loader import read_yaml


class YamlPricingRepository:
    """Loads pricing once from YAML; requests never query an external sheet."""

    def __init__(self, path: Path) -> None:
        raw = read_yaml(path, "pricing")
        try:
            raw["materials"] = {
                code: dict(data, code=code) for code, data in raw.get("materials", {}).items()
            }
            self._catalog = PricingCatalog.model_validate(raw)
        except (ValidationError, TypeError) as exc:
            raise ConfigurationError(f"Invalid pricing configuration: {exc}") from exc

    def get_catalog(self) -> PricingCatalog:
        return self._catalog.model_copy(deep=True)
