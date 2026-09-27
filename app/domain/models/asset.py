from pydantic import BaseModel, Field

from app.domain.enums import UserIntent


class Asset(BaseModel):
    asset_id: str
    kind: str
    description: str
    file: str
    keywords: list[str] = Field(default_factory=list)
    intents: list[UserIntent] = Field(default_factory=list)
    materials: list[str] = Field(default_factory=list)


class AssetQuery(BaseModel):
    message: str
    material_code: str | None = None
    intents: list[UserIntent] = Field(default_factory=list)
    suggested_asset_ids: list[str] = Field(default_factory=list)
