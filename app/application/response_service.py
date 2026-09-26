from app.domain.models.conversation import ConversationState
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

    def assets_for(self, state: ConversationState) -> list[str]:
        ids = ["price_overview", "color_lamos_basic"]
        material = state.slots.get("material_code")
        if material and material.normalized_value == "inox_glass":
            ids.append("sample_inox_glass")
        elif material and material.normalized_value == "picomat_acrylic":
            ids.append("sample_picomat_acrylic")
        return ids
