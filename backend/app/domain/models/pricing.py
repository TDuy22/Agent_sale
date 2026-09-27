from pydantic import BaseModel, Field


class LineItemSpec(BaseModel):
    """How one priced item is measured and whether the customer can opt out of it."""

    name: str
    unit: str = "m"
    length_slot: str | None = None
    toggle_slot: str | None = None


class MaterialPricing(BaseModel):
    code: str
    name: str
    prices: dict[str, int]


class PricingCatalog(BaseModel):
    currency: str = "VND"
    line_items: dict[str, LineItemSpec]
    materials: dict[str, MaterialPricing]
    accessory_packages: dict[str, int] = Field(default_factory=dict)
    appliances: dict[str, int] = Field(default_factory=dict)
