from decimal import ROUND_HALF_UP, Decimal
from uuid import uuid4

from app.application.ports import PricingRepository
from app.domain.enums import QuoteStatus
from app.domain.exceptions import QuoteValidationError
from app.domain.models.conversation import ConversationState
from app.domain.models.quote import Quote, QuoteLine


class QuotationService:
    """Deterministic quotation engine. No language model is used here."""

    def __init__(self, pricing_repository: PricingRepository) -> None:
        self._catalog = pricing_repository.get_catalog()

    def create_quote(self, state: ConversationState, version: int) -> Quote:
        material_code = self._slot(state, "material_code")
        base_length = self._slot(state, "kitchen_length_m")
        missing = [
            name
            for name, value in (
                ("material_code", material_code),
                ("kitchen_length_m", base_length),
            )
            if value is None
        ]
        if missing:
            raise QuoteValidationError(
                f"Cannot create an exact quote without: {', '.join(missing)}"
            )

        material = self._catalog.materials[str(material_code)]
        base = Decimal(str(base_length))
        assumptions: list[str] = []
        explicit_length_slots = {
            "lower_cabinet": "lower_cabinet_length_m",
            "upper_cabinet": "upper_cabinet_length_m",
            "countertop": "countertop_length_m",
            "backsplash": "backsplash_length_m",
            "led": "led_length_m",
        }
        names = {
            "lower_cabinet": "Tủ dưới",
            "upper_cabinet": "Tủ trên",
            "countertop": "Đá mặt bếp",
            "backsplash": "Đá hoặc tấm ốp bếp",
            "led": "LED, nguồn và cảm biến",
        }
        enabled = {
            "lower_cabinet": True,
            "upper_cabinet": True,
            "countertop": self._slot(state, "include_countertop", True),
            "backsplash": self._slot(state, "include_backsplash", True),
            "led": self._slot(state, "include_led", True),
        }

        lines: list[QuoteLine] = []
        used_base_for: list[str] = []
        for code, price in material.prices.items():
            if code not in explicit_length_slots or not enabled.get(code, False):
                continue
            explicit = self._slot(state, explicit_length_slots[code])
            quantity = Decimal(str(explicit)) if explicit is not None else base
            if explicit is None:
                used_base_for.append(names[code])
            total = int((quantity * Decimal(price)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))
            lines.append(
                QuoteLine(
                    code=code,
                    name=names[code],
                    description=f"{names[code]} - {material.name}",
                    unit="m",
                    quantity=quantity,
                    unit_price=price,
                    line_total=total,
                )
            )

        if used_base_for:
            assumptions.append(
                "Dùng chiều dài bếp tổng cho các hạng mục chưa có kích thước riêng: "
                + ", ".join(used_base_for)
                + "."
            )

        accessory_code = self._slot(state, "accessory_package")
        accessory_total = (
            self._catalog.accessory_packages.get(str(accessory_code), 0) if accessory_code else 0
        )
        appliance_codes = self._slot(state, "appliances", [])
        appliance_total = sum(
            self._catalog.appliances.get(str(code), 0) for code in appliance_codes
        )
        subtotal = sum(line.line_total for line in lines)
        return Quote(
            quote_id=str(uuid4()),
            session_id=state.session_id,
            material_code=str(material_code),
            line_items=lines,
            subtotal=subtotal,
            accessory_total=accessory_total,
            appliance_total=appliance_total,
            grand_total=subtotal + accessory_total + appliance_total,
            currency=self._catalog.currency,
            assumptions=assumptions,
            missing_information=[],
            status=QuoteStatus.READY,
            version=version,
        )

    @staticmethod
    def _slot(state: ConversationState, name: str, default: object = None) -> object:
        slot = state.slots.get(name)
        return slot.normalized_value if slot is not None else default
