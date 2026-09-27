from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from app.domain.exceptions import ConfigurationError
from app.domain.models.asset import Asset


class YamlAssetRepository:
    """Metadata-only asset repository; it intentionally does not load image files."""

    def __init__(self, path: str | Path) -> None:
        try:
            raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
            self._assets = self._parse_assets(raw.get("assets", []))
        except (OSError, yaml.YAMLError, ValidationError, TypeError) as exc:
            raise ConfigurationError(f"Cannot load asset configuration: {exc}") from exc

    @staticmethod
    def _parse_assets(raw_assets: Any) -> dict[str, Asset]:
        if isinstance(raw_assets, dict):
            items = [dict(data, id=asset_id) for asset_id, data in raw_assets.items()]
        elif isinstance(raw_assets, list):
            items = raw_assets
        else:
            raise TypeError("assets must be a list or mapping")
        return {
            item["id"]: Asset(asset_id=item["id"], **{k: v for k, v in item.items() if k != "id"})
            for item in items
        }

    def get(self, asset_id: str) -> Asset | None:
        asset = self._assets.get(asset_id)
        return asset.model_copy(deep=True) if asset else None

    def list_assets(self) -> list[Asset]:
        return [asset.model_copy(deep=True) for asset in self._assets.values()]

    def list_ids(self) -> list[str]:
        return list(self._assets)
