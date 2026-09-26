from app.infrastructure.llm.rule_based_extractor import RuleBasedSlotExtractor


def _as_dict(message: str) -> dict[str, object]:
    extraction = RuleBasedSlotExtractor().extract(message)
    return {slot.name: slot.value for slot in extraction.extracted_slots}


def test_recognizes_decimal_correction() -> None:
    result = RuleBasedSlotExtractor().extract("Không phải 4m, sửa lại thành 3,5 mét.")
    values = {slot.name: slot.value for slot in result.extracted_slots}
    assert values["kitchen_length_m"] == "3.5"
    assert "kitchen_length_m" in result.corrections


def test_recognizes_specific_upper_cabinet_length() -> None:
    assert _as_dict("Tủ trên chỉ 3m thôi.")["upper_cabinet_length_m"] == "3"


def test_recognizes_negative_options() -> None:
    values = _as_dict("Không lấy đá mặt bếp, không LED nhưng có kính ốp.")
    assert values["include_countertop"] is False
    assert values["include_led"] is False
    assert values["include_backsplash"] is True
