import re

from app.domain.enums import UserIntent
from app.domain.models.conversation import ExtractedSlot, SlotExtractionResult
from app.infrastructure.text import fold


def _number(raw: str) -> str:
    return raw.replace(",", ".")


class RuleBasedSlotExtractor:
    """Deterministic Vietnamese extractor used without external services."""

    name = "rule_based"
    _measurement = r"(?P<value>\d+(?:[\.,]\d+)?)\s*(?:m|met|mét)\b"

    def extract(self, message: str) -> SlotExtractionResult:
        lowered = message.lower()
        folded = fold(message)
        slots: dict[str, ExtractedSlot] = {}
        corrections: list[str] = []
        intents: list[UserIntent] = []

        if "xay moi" in folded:
            slots["project_type"] = ExtractedSlot(name="project_type", value="new_build")
        elif "cai tao" in folded or "sua lai bep" in folded:
            slots["project_type"] = ExtractedSlot(name="project_type", value="renovation")

        if "inox canh kinh" in folded:
            slots["material_code"] = ExtractedSlot(name="material_code", value="inox_glass")
        elif "picomat" in folded and "acrylic" in folded:
            slots["material_code"] = ExtractedSlot(name="material_code", value="picomat_acrylic")

        color_aliases = {
            "ghi xam": "gray",
            "xam": "gray",
            "ghi": "gray",
            "trang": "white",
            "den": "black",
            "xanh": "blue",
            "kem": "beige",
            "nau": "brown",
            "vang": "yellow",
        }
        color_match = re.search(r"\bmau\s+(ghi xam|xam|ghi|trang|den|xanh|kem|nau|vang)\b", folded)
        if color_match:
            slots["color"] = ExtractedSlot(name="color", value=color_aliases[color_match.group(1)])

        correction = re.search(
            rf"(?:khong phai\s+\d+(?:[\.,]\d+)?\s*(?:m|met)|sua(?: lai)?).*?"
            rf"(?:thanh|la)\s*{self._measurement}",
            folded,
        )
        if correction:
            slots["kitchen_length_m"] = ExtractedSlot(
                name="kitchen_length_m", value=_number(correction.group("value"))
            )
            corrections.append("kitchen_length_m")

        dimension_patterns = {
            "lower_cabinet_length_m": rf"tu duoi\D{{0,20}}{self._measurement}",
            "upper_cabinet_length_m": rf"tu tren\D{{0,20}}{self._measurement}",
            "countertop_length_m": rf"(?:da mat bep|mat da)\D{{0,20}}{self._measurement}",
            "backsplash_length_m": rf"(?:kinh op|op bep)\D{{0,20}}{self._measurement}",
            "led_length_m": rf"led\D{{0,20}}{self._measurement}",
        }
        has_specific_dimension = False
        for name, pattern in dimension_patterns.items():
            match = re.search(pattern, folded)
            if match:
                has_specific_dimension = True
                slots[name] = ExtractedSlot(name=name, value=_number(match.group("value")))
                if re.search(r"\b(?:sua|chi|thoi)\b", folded):
                    corrections.append(name)

        if "kitchen_length_m" not in slots and not has_specific_dimension:
            match = re.search(self._measurement, folded)
            if match:
                slots["kitchen_length_m"] = ExtractedSlot(
                    name="kitchen_length_m", value=_number(match.group("value"))
                )

        self._extract_options(folded, slots)
        if any(term in lowered for term in ("xem màu", "bảng màu", "màu kính")):
            intents.append(UserIntent.SHOW_COLOR)
        if any(
            term in lowered for term in ("xem mẫu", "mẫu tủ", "xem hình", "hình thực tế", "mẫu bếp")
        ):
            intents.append(UserIntent.SHOW_SAMPLE)
        if any(term in folded for term in ("xem phu kien", "mau phu kien")):
            intents.append(UserIntent.SHOW_ACCESSORIES)
        if any(term in folded for term in ("bao gia", "tinh gia", "tong tien")):
            intents.append(UserIntent.REQUEST_QUOTE)
        return SlotExtractionResult(
            extracted_slots=list(slots.values()),
            corrections=list(dict.fromkeys(corrections)),
            intents=list(dict.fromkeys(intents)),
            confidence=0.95 if slots else 0.0,
        )

    @staticmethod
    def _extract_options(folded: str, slots: dict[str, ExtractedSlot]) -> None:
        option_terms = {
            "include_countertop": ("da mat bep", "mat da"),
            "include_backsplash": ("kinh op", "op bep"),
            "include_led": ("led",),
        }
        for name, terms in option_terms.items():
            for term in terms:
                if term not in folded:
                    continue
                negative = re.search(rf"(?:khong|bo|chua)\s+(?:lay\s+|can\s+)?{term}", folded)
                slots[name] = ExtractedSlot(name=name, value=not bool(negative))
                break

        if "goi phu kien tieu chuan" in folded or "phu kien standard" in folded:
            slots["accessory_package"] = ExtractedSlot(name="accessory_package", value="standard")

        appliances: list[str] = []
        if "may hut mui" in folded:
            appliances.append("hood")
        if "bep tu" in folded:
            appliances.append("hob")
        if appliances:
            slots["appliances"] = ExtractedSlot(name="appliances", value=appliances)
