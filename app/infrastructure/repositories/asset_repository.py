from pathlib import Path

import yaml

from app.domain.exceptions import ConfigurationError
from app.domain.models.asset import Asset


class YamlAssetRepository:
    """Metadata-only asset repository; it intentionally does not load image files."""

    def __init__(self, path: str | Path) -> None:
        try:
            raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
            self._assets = {
                asset_id: Asset(asset_id=asset_id, **data)
                for asset_id, data in raw.get("assets", {}).items()
            }
        except (OSError, yaml.YAMLError, TypeError) as exc:
            raise ConfigurationError(f"Cannot load asset configuration: {exc}") from exc

    def get(self, asset_id: str) -> Asset | None:
        asset = self._assets.get(asset_id)
        return asset.model_copy(deep=True) if asset else None

    def list_ids(self) -> list[str]:
        return list(self._assets)
