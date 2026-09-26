from pydantic import BaseModel, Field


class MaterialPricing(BaseModel):
    code: str
    name: str
    prices: dict[str, int]


class PricingCatalog(BaseModel):
    currency: str = "VND"
    materials: dict[str, MaterialPricing]
    accessory_packages: dict[str, int] = Field(default_factory=dict)
    appliances: dict[str, int] = Field(default_factory=dict)
