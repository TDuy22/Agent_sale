import logging
from pathlib import Path
from typing import Any

import streamlit as st

from app.application.chat_service import ChatService
from app.container import build_chat_service, get_asset_repository
from app.domain.models.quote import Quote
from app.infrastructure.repositories.asset_repository import YamlAssetRepository
from app.settings import get_settings

logger = logging.getLogger(__name__)


def _money(value: int) -> str:
    return f"{value:,}".replace(",", ".") + " VNĐ"


@st.cache_resource
def _resources() -> tuple[ChatService, YamlAssetRepository]:
    return build_chat_service(), get_asset_repository()


def _render_quote(quote: Quote) -> None:
    material_names = {
        "inox_glass": "Inox cánh kính",
        "picomat_acrylic": "Nhựa Picomat cánh Acrylic",
    }
    st.markdown("#### Báo giá tạm tính")
    st.write(f"**Vật liệu:** {material_names.get(quote.material_code, quote.material_code)}")
    st.table(
        [
            {
                "Hạng mục": line.name,
                "Khối lượng": f"{line.quantity} {line.unit}",
                "Đơn giá": _money(line.unit_price),
                "Thành tiền": _money(line.line_total),
            }
            for line in quote.line_items
        ]
    )
    st.metric("Tổng", _money(quote.grand_total))
    if quote.assumptions:
        st.caption("Giả định: " + " ".join(quote.assumptions))


def _render_assets(asset_ids: list[str], repository: YamlAssetRepository) -> None:
    for asset_id in asset_ids:
        asset = repository.get(asset_id)
        if asset is None:
            continue
        image_path = Path(asset.file)
        if image_path.is_file():
            st.image(str(image_path), caption=asset.description, use_container_width=True)


def _render_message(message: dict[str, Any], repository: YamlAssetRepository) -> None:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        _render_assets(message.get("asset_ids", []), repository)
        quote = message.get("quote")
        if quote is not None:
            _render_quote(quote)


def _new_session(service: ChatService) -> str:
    state = service.create_session()
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": (
                "Em chào anh/chị. Anh/chị đang xây mới hay cải tạo bếp, và đã chọn "
                "vật liệu nào chưa ạ?"
            ),
            "asset_ids": [],
            "quote": None,
        }
    ]
    return state.session_id


def main() -> None:
    st.set_page_config(page_title="AI Sales Agent", page_icon="🏠", layout="wide")
    service, asset_repository = _resources()
    settings = get_settings()

    if "session_id" not in st.session_state:
        st.session_state.session_id = _new_session(service)

    st.title("AI Sales Agent — Tư vấn tủ bếp")
    st.caption("Demo local: flow → memory → asset → quotation")

    with st.sidebar:
        st.subheader("Conversation state")
        if st.button("Tạo hội thoại mới", use_container_width=True):
            st.session_state.session_id = _new_session(service)
            st.rerun()
        state = service.get_session(st.session_state.session_id)
        if settings.slot_extractor.lower() == "gemini":
            extractor_label = f"Gemini — {settings.gemini_model}"
        elif settings.slot_extractor.lower() == "openai":
            extractor_label = f"OpenAI — {settings.openai_model}"
        else:
            extractor_label = settings.slot_extractor
        st.caption(f"Extractor: {extractor_label}")
        st.write(f"**Section:** `{state.current_section}`")
        st.write(f"**Status:** `{state.status.value}`")
        st.write("**Collected slots**")
        st.json({name: slot.normalized_value for name, slot in state.slots.items()})

    for message in st.session_state.messages:
        _render_message(message, asset_repository)

    if prompt := st.chat_input("Nhập nhu cầu của khách..."):
        user_message = {
            "role": "user",
            "content": prompt,
            "asset_ids": [],
            "quote": None,
        }
        st.session_state.messages.append(user_message)
        _render_message(user_message, asset_repository)
        try:
            with st.spinner("AI đang phân tích nhu cầu..."):
                result = service.chat(prompt, st.session_state.session_id)
            assistant_message = {
                "role": "assistant",
                "content": result.reply,
                "asset_ids": result.asset_ids,
                "quote": result.quote,
            }
        except Exception:
            logger.exception("The chat request failed")
            assistant_message = {
                "role": "assistant",
                "content": (
                    "Dịch vụ AI đang bận hoặc tạm thời mất kết nối. "
                    "Anh/chị vui lòng gửi lại tin nhắn sau ít giây."
                ),
                "asset_ids": [],
                "quote": None,
            }
        st.session_state.messages.append(assistant_message)
        _render_message(assistant_message, asset_repository)


if __name__ == "__main__":
    main()
