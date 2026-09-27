from decimal import Decimal

from app.application.chat_service import ChatService
from app.domain.enums import ConversationStatus


def test_extracts_multiple_sections_from_one_message(service: ChatService) -> None:
    state = service.create_session()

    result = service.chat("Nhà anh xây mới, làm inox cánh kính màu xám 4m.", state.session_id)

    assert result.collected_slots["project_type"].normalized_value == "new_build"
    assert result.collected_slots["material_code"].normalized_value == "inox_glass"
    assert result.collected_slots["kitchen_length_m"].normalized_value == Decimal("4")
    assert {"project_info", "material", "dimensions"}.issubset(result.completed_sections)
    assert result.missing_slots == []


def test_collects_dimension_across_turns_without_losing_memory(
    service: ChatService,
) -> None:
    state = service.create_session()
    first = service.chat("Nhà xây mới, dùng inox cánh kính.", state.session_id)
    assert first.current_section == "dimensions"
    assert first.missing_slots == ["kitchen_length_m"]

    second = service.chat("Kích thước cũng bình thường thôi.", state.session_id)
    assert second.current_section == "dimensions"
    assert second.attempts["dimensions"].failed_attempt_count == 1

    third = service.chat("4m", state.session_id)
    assert third.current_section == "color"
    assert third.collected_slots["project_type"].normalized_value == "new_build"
    assert third.attempts["dimensions"].failed_attempt_count == 1

    quoted = service.chat("Màu xám.", state.session_id)
    assert quoted.status == ConversationStatus.QUOTED.value


def test_three_failed_dimension_answers_require_human(service: ChatService) -> None:
    state = service.create_session()
    service.chat("Nhà xây mới, dùng inox cánh kính.", state.session_id)

    service.chat("Chưa rõ.", state.session_id)
    service.chat("Tôi không biết.", state.session_id)
    result = service.chat("Để tính sau.", state.session_id)

    assert result.status == ConversationStatus.NEEDS_HUMAN.value
    assert result.quote is None
    assert result.attempts["dimensions"].failed_attempt_count == 3


def test_correction_replaces_dimension_and_recalculates_quote(
    service: ChatService,
) -> None:
    state = service.create_session()
    initial = service.chat("Nhà xây mới, làm inox cánh kính màu xám 4m.", state.session_id)
    assert initial.quote is not None
    assert initial.quote.version == 1
    assert initial.quote.subtotal == 44_800_000

    corrected = service.chat("Không phải 4m, sửa lại thành 3,5m.", state.session_id)

    assert corrected.collected_slots["kitchen_length_m"].normalized_value == Decimal("3.5")
    assert corrected.quote is not None
    assert corrected.quote.version == 2
    assert corrected.quote.subtotal == 39_200_000


def test_off_topic_answer_keeps_section_and_memory(service: ChatService) -> None:
    state = service.create_session()
    first = service.chat("Nhà tôi xây mới.", state.session_id)
    assert first.current_section == "material"

    result = service.chat("Hôm nay trời đẹp quá.", state.session_id)

    assert result.current_section == "material"
    assert result.missing_slots == ["material_code"]
    assert result.collected_slots["project_type"].normalized_value == "new_build"


def test_future_section_data_is_saved_and_used_later(service: ChatService) -> None:
    state = service.create_session()
    early = service.chat("Muốn làm inox cánh kính 4m và có LED.", state.session_id)
    assert early.current_section == "project_info"
    assert early.collected_slots["material_code"].normalized_value == "inox_glass"
    assert early.collected_slots["kitchen_length_m"].normalized_value == Decimal("4")

    result = service.chat("Nhà xây mới, màu xám.", state.session_id)

    assert result.quote is not None
    assert result.missing_slots == []
    assert {"project_info", "material", "dimensions", "color"}.issubset(result.completed_sections)


def test_specific_length_overrides_kitchen_length(service: ChatService) -> None:
    state = service.create_session()
    service.chat("Muốn tủ trên chỉ 3m thôi.", state.session_id)

    result = service.chat("Nhà xây mới, làm inox cánh kính màu xám, bếp dài 4m.", state.session_id)

    assert result.quote is not None
    upper_line = next(line for line in result.quote.line_items if line.code == "upper_cabinet")
    assert upper_line.quantity == Decimal("3")
    assert result.quote.subtotal == 40_600_000
