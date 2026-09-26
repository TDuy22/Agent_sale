from pathlib import Path

import yaml
from pydantic import ValidationError

from app.domain.exceptions import ConfigurationError
from app.domain.models.pricing import MaterialPricing, PricingCatalog


class YamlPricingRepository:
    """Loads pricing once from YAML; requests never query an external sheet."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._catalog = self._load()

    def _load(self) -> PricingCatalog:
        try:
            raw = yaml.safe_load(self._path.read_text(encoding="utf-8"))
            raw["materials"] = {
                code: MaterialPricing(code=code, **data)
                for code, data in raw.get("materials", {}).items()
            }
            return PricingCatalog.model_validate(raw)
        except (OSError, yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigurationError(f"Cannot load pricing configuration: {exc}") from exc

    def get_catalog(self) -> PricingCatalog:
        return self._catalog.model_copy(deep=True)
