from app.domain.models.asset import Asset
from app.domain.models.quote import Quote


class ResponseService:
    """Creates user-facing Vietnamese text without exposing internal reasoning."""

    def __init__(self, slot_labels: dict[str, str]) -> None:
        self._labels = slot_labels

    def ask_for(self, missing_fields: list[str]) -> str:
        labels = self._label(missing_fields)
        if len(labels) == 1:
            return f"Anh/chị vui lòng cho biết {labels[0]}?"
        return "Anh/chị vui lòng cho biết: " + "; ".join(labels) + "."

    def needs_human(self, missing_fields: list[str]) -> str:
        return (
            "Em chưa xác định được "
            + ", ".join(self._label(missing_fields))
            + ". Em sẽ chuyển thông tin cho tư vấn viên hỗ trợ anh/chị."
        )

    def quote_ready(self, quote: Quote) -> str:
        total = f"{quote.grand_total:,}".replace(",", ".")
        return (
            f"Báo giá tạm tính phiên bản {quote.version}: {total} {quote.currency}. "
            "Chi tiết từng hạng mục ở bảng bên dưới."
        )

    def completed(self) -> str:
        return "Phiên tư vấn đã hoàn tất."

    def with_assets(self, reply: str, assets: list[Asset]) -> str:
        return f"{assets[0].intro} {reply}" if assets else reply

    def _label(self, names: list[str]) -> list[str]:
        return [self._labels.get(name, name) for name in names]
