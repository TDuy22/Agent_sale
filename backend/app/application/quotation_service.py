from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from app.application.ports import PricingRepository
from app.domain.exceptions import QuoteValidationError
from app.domain.models.conversation import ConversationState
from app.domain.models.quote import Quote, QuoteLine


class QuotationService:
    """Deterministic quotation engine driven by the pricing catalog. No LLM is used here."""

    def __init__(self, pricing_repository: PricingRepository) -> None:
        self._catalog = pricing_repository.get_catalog()

    def create_quote(self, state: ConversationState, version: int) -> Quote:
        material_code = self._slot(state, "material_code")
        base_length = self._slot(state, "kitchen_length_m")
        missing = [
            name
            for name, value in (("material_code", material_code), ("kitchen_length_m", base_length))
            if value is None
        ]
        if missing:
            raise QuoteValidationError(
                f"Cannot create an exact quote without: {', '.join(missing)}"
            )

        material = self._catalog.materials[str(material_code)]
        base = Decimal(str(base_length))
        lines: list[QuoteLine] = []
        used_base_for: list[str] = []
        for code, spec in self._catalog.line_items.items():
            price = material.prices.get(code)
            if price is None:
                continue
            if spec.toggle_slot and not self._slot(state, spec.toggle_slot, True):
                continue
            explicit = self._slot(state, spec.length_slot) if spec.length_slot else None
            if explicit is None:
                used_base_for.append(spec.name)
            quantity = Decimal(str(explicit)) if explicit is not None else base
            total = int((quantity * price).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            lines.append(
                QuoteLine(
                    code=code,
                    name=spec.name,
                    description=f"{spec.name} - {material.name}",
                    unit=spec.unit,
                    quantity=quantity,
                    unit_price=price,
                    line_total=total,
                )
            )

        assumptions = []
        if used_base_for:
            assumptions.append(
                "Dùng chiều dài bếp tổng cho các hạng mục chưa có kích thước riêng: "
                + ", ".join(used_base_for)
                + "."
            )

        accessory_code = self._slot(state, "accessory_package")
        accessory_total = self._catalog.accessory_packages.get(str(accessory_code), 0)
        appliance_total = sum(
            self._catalog.appliances.get(str(code), 0)
            for code in self._slot(state, "appliances", [])
        )
        subtotal = sum(line.line_total for line in lines)
        return Quote(
            quote_id=str(uuid4()),
            session_id=state.session_id,
            material_code=material.code,
            material_name=material.name,
            line_items=lines,
            subtotal=subtotal,
            accessory_total=accessory_total,
            appliance_total=appliance_total,
            grand_total=subtotal + accessory_total + appliance_total,
            currency=self._catalog.currency,
            assumptions=assumptions,
            version=version,
        )

    @staticmethod
    def _slot(state: ConversationState, name: str, default: object = None) -> object:
        slot = state.slots.get(name)
        return slot.normalized_value if slot is not None else default
