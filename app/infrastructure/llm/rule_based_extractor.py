import re
import unicodedata

from app.domain.models.conversation import ExtractedSlot, SlotExtractionResult


def _fold(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    folded = "".join(char for char in normalized if unicodedata.category(char) != "Mn")
    return folded.replace("đ", "d")


def _number(raw: str) -> str:
    return raw.replace(",", ".")


class RuleBasedSlotExtractor:
    """Deterministic Vietnamese extractor used without external services."""

    _measurement = r"(?P<value>\d+(?:[\.,]\d+)?)\s*(?:m|met|mét)\b"

    def extract(self, message: str) -> SlotExtractionResult:
        folded = _fold(message)
        slots: dict[str, ExtractedSlot] = {}
        corrections: list[str] = []

        if "xay moi" in folded:
            slots["project_type"] = ExtractedSlot(name="project_type", value="new_build")
        elif "cai tao" in folded or "sua lai bep" in folded:
            slots["project_type"] = ExtractedSlot(name="project_type", value="renovation")

        if "inox canh kinh" in folded:
            slots["material_code"] = ExtractedSlot(name="material_code", value="inox_glass")
        elif "picomat" in folded and "acrylic" in folded:
            slots["material_code"] = ExtractedSlot(name="material_code", value="picomat_acrylic")

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
                if any(word in folded for word in ("sua", "chi", "thoi")):
                    corrections.append(name)

        if "kitchen_length_m" not in slots and not has_specific_dimension:
            match = re.search(self._measurement, folded)
            if match:
                slots["kitchen_length_m"] = ExtractedSlot(
                    name="kitchen_length_m", value=_number(match.group("value"))
                )

        self._extract_options(folded, slots)
        return SlotExtractionResult(
            extracted_slots=list(slots.values()),
            corrections=list(dict.fromkeys(corrections)),
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
