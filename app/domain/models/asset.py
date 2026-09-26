from pydantic import BaseModel


class Asset(BaseModel):
    asset_id: str
    kind: str
    description: str
