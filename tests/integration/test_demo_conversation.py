from decimal import Decimal

from app.application.chat_service import ChatService


def test_demo_flow_memory_assets_and_quote(service: ChatService) -> None:
    state = service.create_session()

    need = service.chat(
        "Nhà anh xây mới muốn làm tủ inox cánh kính 4m",
        state.session_id,
    )
    assert need.collected_slots["material_code"].normalized_value == "inox_glass"
    assert need.collected_slots["kitchen_length_m"].normalized_value == Decimal("4")
    assert need.current_section == "color"

    sample = service.chat("Cho anh xem mẫu", state.session_id)
    assert sample.asset_ids == ["kitchen_sample_combined"]
    assert sample.current_section == "color"

    colors = service.chat("Cho anh xem màu", state.session_id)
    assert colors.asset_ids == ["color_sample_combined"]
    assert colors.current_section == "color"

    quoted = service.chat("Anh chọn màu xám", state.session_id)
    assert quoted.collected_slots["color"].normalized_value == "gray"
    assert quoted.quote is not None
    assert quoted.quote.grand_total == 44_800_000
    assert quoted.asset_ids == ["color_sample_combined"]
    assert "bảng màu kính" in quoted.reply
