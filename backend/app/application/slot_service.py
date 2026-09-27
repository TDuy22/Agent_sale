from decimal import Decimal, InvalidOperation
from typing import Any

from app.application.ports import PricingRepository
from app.domain.models.conversation import (
    ConversationState,
    SlotExtractionResult,
    SlotValue,
)


class SlotService:
    """Normalizes, validates, and merges extracted values into structured memory."""

    LENGTH_SLOTS = {
        "kitchen_length_m",
        "lower_cabinet_length_m",
        "upper_cabinet_length_m",
        "countertop_length_m",
        "backsplash_length_m",
        "led_length_m",
    }
    BOOLEAN_SLOTS = {"include_countertop", "include_backsplash", "include_led"}
    OTHER_SLOTS = {
        "project_type",
        "material_code",
        "location",
        "color",
        "accessory_package",
        "appliances",
    }

    def __init__(self, pricing_repository: PricingRepository) -> None:
        self._catalog = pricing_repository.get_catalog()

    def merge(
        self,
        state: ConversationState,
        extraction: SlotExtractionResult,
        source_message: str,
    ) -> tuple[set[str], bool]:
        accepted: set[str] = set()
        changed_any = False
        known = self.LENGTH_SLOTS | self.BOOLEAN_SLOTS | self.OTHER_SLOTS
        for candidate in extraction.extracted_slots:
            if candidate.name not in known:
                continue
            try:
                normalized = self.normalize(candidate.name, candidate.value)
            except (InvalidOperation, TypeError, ValueError):
                continue
            if not self.is_valid(candidate.name, normalized):
                continue
            previous = state.slots.get(candidate.name)
            if previous is None or previous.normalized_value != normalized:
                changed_any = True
            state.slots[candidate.name] = SlotValue(
                value=candidate.value,
                normalized_value=normalized,
                source_message=source_message,
                confidence=candidate.confidence,
            )
            accepted.add(candidate.name)
        return accepted, changed_any

    def apply_defaults(
        self, state: ConversationState, defaults: dict[str, Any], section_id: str
    ) -> set[str]:
        added: set[str] = set()
        for name, value in defaults.items():
            if name in state.slots:
                continue
            normalized = self.normalize(name, value)
            state.slots[name] = SlotValue(
                value=value,
                normalized_value=normalized,
                source_message=f"flow_default:{section_id}",
                confidence=1.0,
            )
            added.add(name)
        return added

    def missing_or_invalid(self, state: ConversationState, names: list[str]) -> list[str]:
        return [
            name
            for name in names
            if name not in state.slots
            or not self.is_valid(name, state.slots[name].normalized_value)
        ]

    def normalize(self, name: str, value: Any) -> Any:
        if name in self.LENGTH_SLOTS:
            return Decimal(str(value).replace(",", "."))
        if name in self.BOOLEAN_SLOTS:
            if isinstance(value, bool):
                return value
            folded = str(value).strip().lower()
            if folded in {"true", "yes", "1", "có", "co"}:
                return True
            if folded in {"false", "no", "0", "không", "khong"}:
                return False
            raise ValueError(f"Invalid boolean for {name}")
        if name == "appliances":
            return list(value) if isinstance(value, list) else [str(value)]
        return str(value).strip()

    def is_valid(self, name: str, value: Any) -> bool:
        if name in self.LENGTH_SLOTS:
            return isinstance(value, Decimal) and value > 0
        if name in self.BOOLEAN_SLOTS:
            return isinstance(value, bool)
        if name == "project_type":
            return value in {"new_build", "renovation"}
        if name == "material_code":
            return value in self._catalog.materials
        if name == "accessory_package":
            return value in self._catalog.accessory_packages
        if name == "appliances":
            return isinstance(value, list) and all(
                item in self._catalog.appliances for item in value
            )
        return bool(value)
