from decimal import Decimal

from pydantic import BaseModel, Field


class QuoteLine(BaseModel):
    code: str
    name: str
    description: str
    unit: str
    quantity: Decimal
    unit_price: int
    line_total: int


class Quote(BaseModel):
    quote_id: str
    session_id: str
    material_code: str
    material_name: str
    line_items: list[QuoteLine] = Field(default_factory=list)
    subtotal: int
    accessory_total: int = 0
    appliance_total: int = 0
    grand_total: int
    currency: str = "VND"
    assumptions: list[str] = Field(default_factory=list)
    version: int
