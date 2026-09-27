from app.domain.enums import UserIntent
from app.domain.models.quote import Quote


class ResponseService:
    """Creates user-facing Vietnamese text without exposing internal reasoning."""

    FIELD_LABELS = {
        "project_type": "công trình là xây mới hay cải tạo",
        "material_code": "vật liệu tủ bếp mong muốn",
        "kitchen_length_m": "chiều dài bếp (mét)",
        "lower_cabinet_length_m": "chiều dài tủ dưới",
        "upper_cabinet_length_m": "chiều dài tủ trên",
        "countertop_length_m": "chiều dài đá mặt bếp",
        "backsplash_length_m": "chiều dài phần ốp bếp",
        "led_length_m": "chiều dài LED",
        "color": "màu cánh tủ mong muốn",
    }

    def ask_for(self, missing_fields: list[str]) -> str:
        labels = [self.FIELD_LABELS.get(name, name) for name in missing_fields]
        if len(labels) == 1:
            return f"Anh/chị vui lòng cho biết {labels[0]}?"
        return "Anh/chị vui lòng cho biết: " + "; ".join(labels) + "."

    def needs_human(self, missing_fields: list[str]) -> str:
        labels = [self.FIELD_LABELS.get(name, name) for name in missing_fields]
        return (
            "Tôi chưa xác định được "
            + ", ".join(labels)
            + ". Tôi sẽ chuyển thông tin cho tư vấn viên hỗ trợ."
        )

    def quote_ready(self, quote: Quote) -> str:
        total = f"{quote.grand_total:,}".replace(",", ".")
        return (
            f"Báo giá tạm tính phiên bản {quote.version}: {total} {quote.currency}. "
            "Chi tiết hạng mục đã được trả trong trường quote."
        )

    def with_assets(
        self,
        reply: str,
        intents: list[UserIntent],
        asset_ids: list[str],
    ) -> str:
        if UserIntent.SHOW_COLOR in intents or "color_sample_combined" in asset_ids:
            intro = "Em gửi anh/chị bảng màu kính để tham khảo."
        elif UserIntent.SHOW_ACCESSORIES in intents or "accessory_sample_combined" in asset_ids:
            intro = "Em gửi anh/chị ảnh các phụ kiện tủ bếp để tham khảo."
        else:
            intro = "Em gửi anh/chị ảnh mẫu tủ bếp thực tế để tham khảo."
        return f"{intro} {reply}"
