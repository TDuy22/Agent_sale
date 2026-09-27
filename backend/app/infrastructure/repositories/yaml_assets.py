from pathlib import Path

from pydantic import ValidationError

from app.domain.exceptions import ConfigurationError
from app.domain.models.asset import Asset
from app.infrastructure.repositories.yaml_loader import read_yaml


class YamlAssetRepository:
    """Asset metadata from YAML; image paths resolve relative to the YAML file."""

    def __init__(self, path: Path) -> None:
        raw = read_yaml(path, "asset")
        try:
            assets = [
                Asset(
                    asset_id=item["id"],
                    file=(path.parent / item["file"]).resolve(),
                    **{key: value for key, value in item.items() if key not in {"id", "file"}},
                )
                for item in raw.get("assets", [])
            ]
        except (ValidationError, KeyError, TypeError) as exc:
            raise ConfigurationError(f"Invalid asset configuration: {exc}") from exc
        self._assets = {asset.asset_id: asset for asset in assets}

    def get(self, asset_id: str) -> Asset | None:
        asset = self._assets.get(asset_id)
        return asset.model_copy(deep=True) if asset else None

    def list_assets(self) -> list[Asset]:
        return [asset.model_copy(deep=True) for asset in self._assets.values()]
