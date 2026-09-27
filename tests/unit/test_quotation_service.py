import pytest

from app.application.chat_service import ChatService


@pytest.mark.parametrize(
    ("message", "expected_subtotal"),
    [
        ("Nhà xây mới, inox cánh kính màu xám 3m.", 33_600_000),
        ("Nhà xây mới, inox cánh kính màu xám 4m.", 44_800_000),
        ("Nhà cải tạo, nhựa Picomat cánh Acrylic màu trắng 3m.", 28_200_000),
    ],
)
def test_seed_pricing_totals(service: ChatService, message: str, expected_subtotal: int) -> None:
    state = service.create_session()

    result = service.chat(message, state.session_id)

    assert result.quote is not None
    assert result.quote.subtotal == expected_subtotal
    assert result.quote.grand_total == expected_subtotal
    assert result.quote.assumptions
