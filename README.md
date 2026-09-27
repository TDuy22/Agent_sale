# Interior Quotation Chatbot

Demo local cho chatbot tư vấn và báo giá tủ bếp theo finite-state workflow. Ứng dụng hỗ
trợ Gemini, OpenAI structured output và rule-based extractor chạy hoàn toàn local.

## Kiến trúc

```text
HTTP / CLI / Streamlit UI
    -> ChatService
        -> SlotExtractor (Gemini, OpenAI hoặc rule-based)
        -> FlowEngine (đọc config/flow.yaml)
        -> SlotService (normalize, validate, merge memory)
        -> ImageAssetSkill -> KeywordAssetMatcher -> YAML metadata
        -> QuotationService (Decimal/integer VND, không gọi LLM)
        -> ConversationRepository
```

- `app/domain`: model và enum nghiệp vụ, không biết FastAPI hay Google Sheets.
- `app/application`: orchestration, workflow, slot validation, quotation và ports.
- `app/infrastructure`: YAML loaders, memory repository, extractor adapters.
- `app/api`: request/response schema và route mỏng.
- `config`: flow và pricing có thể thay độc lập.
- `data_image/assets.yaml`: metadata ánh xạ hai ảnh demo theo intent/context.
- `tests`: unit test cho workflow/extraction/pricing và integration test cho API.

Memory nghiệp vụ nằm trong `ConversationState.slots`. Mỗi slot lưu raw value, giá trị
chuẩn hóa, source message, confidence và thời điểm cập nhật. Message history không được
dùng thay thế structured memory.

## Cài môi trường

Yêu cầu Python 3.12.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env
```

Linux/macOS dùng `source .venv/bin/activate` và `cp .env.example .env`.

## Chạy API

```powershell
uvicorn app.main:app --reload
```

Các endpoint:

- `GET /health`
- `POST /api/v1/sessions`
- `GET /api/v1/sessions/{session_id}`
- `POST /api/v1/chat`

Ví dụ:

```json
{
  "message": "Nhà anh xây mới, muốn làm tủ inox cánh kính khoảng 4m"
}
```

Nếu bỏ `session_id`, chat endpoint tự tạo session. Những lượt sau nên gửi lại ID nhận
được để tiếp tục đúng memory.

## Chạy CLI

```powershell
python -m app.cli
```

CLI hỗ trợ `/state`, `/reset` và `/quit`.

## Chạy Local Chat UI

```powershell
streamlit run app/ui.py
```

UI hiển thị hội thoại, section hiện tại, structured slots, ảnh được chọn từ metadata và
bảng chi tiết báo giá. Ảnh được đọc local từ `data_image/`; LLM không nhận đường dẫn và
không trực tiếp chọn file.

## Test và lint

```powershell
python -m pytest
ruff check .
ruff format --check .
```

## Thay đổi flow

Sửa `config/flow.yaml`; `FlowEngine` duyệt danh sách section theo thứ tự và không chứa
chuỗi `if/else` theo từng kịch bản. Mỗi section khai báo `required_slots`,
`optional_slots`, `max_attempts`, `failure_policy`, `suggested_assets` và tùy chọn
`defaults`.

Khi thêm required slot mới:

1. Thêm slot vào YAML.
2. Bổ sung normalize/validation tương ứng trong `SlotService`.
3. Cho extractor trả slot đó.
4. Thêm nhãn câu hỏi trong `ResponseService` và test luồng.

`failed_attempt_count` chỉ tăng khi người dùng không cung cấp slot hợp lệ đang được hỏi;
`turn_count` vẫn ghi tổng số lượt dừng tại section.

## Thêm vật liệu và đơn giá

Thêm material code trong `config/pricing.yaml`, gồm `name` và giá integer VND cho các
code line item. Sau đó bổ sung alias nhận diện trong rule-based extractor hoặc để LLM
extractor trả đúng code. Request không đọc Google Sheets; YAML được load một lần khi tạo
service.

Nếu chỉ có `kitchen_length_m`, MVP dùng chiều dài này cho tủ dưới, tủ trên, mặt đá, ốp
bếp và LED. Quote luôn ghi rõ giả định đó. Chiều dài riêng, nếu có, được ưu tiên.

## Thay memory repository

Tạo adapter mới implement `ConversationRepository` trong `app/application/ports.py`
(ví dụ Redis/PostgreSQL), rồi thay adapter tại `app/container.py`. Domain và FlowEngine
không cần sửa. Adapter production cần bổ sung atomic update/concurrency control.

## Cấu hình LLM extractor

Trong `.env`:

```dotenv
SLOT_EXTRACTOR=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.5-flash-lite

OPENAI_API_KEY=...
OPENAI_MODEL=gpt-5.4-mini
```

`SLOT_EXTRACTOR` nhận `gemini`, `openai`, `rule_based` hoặc `auto`. Model name chỉ đến
từ biến môi trường, không hardcode trong adapter. Khi cấu hình provider được chọn chưa
đủ key/model, ứng dụng dùng rule-based extractor.

Các adapter dùng Pydantic structured output; LLM chỉ trích xuất slot, normalize và phân
loại intent, không chuyển section, không chọn file và không tính giá. Material code lạ
tiếp tục bị `SlotService` từ chối. Xem tài liệu structured output chính thức của
[Gemini](https://ai.google.dev/gemini-api/docs/structured-output) và
[OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs).

## Image Asset Skill

Mỗi asset trong `data_image/assets.yaml` có `id`, `file`, `description`, `keywords`,
`intents` và `materials`. `ImageAssetSkill` tạo query từ conversation state; matcher xác
định asset theo suggestion của section, intent và keyword. Để thêm ảnh, chỉ cần đặt file
local và thêm một record metadata, không cần sửa flow engine.

## Chưa triển khai

- Đồng bộ Google Sheets/OAuth; `scripts/import_pricing_sheet.py` chỉ là skeleton.
- Database/Redis persistence và locking đa process.
- UI production, auth production, Messenger/Zalo.
- OCR/bản vẽ, RAG/vector database.
- Sinh PDF/ảnh và upload asset thật.
- Admin UI, audit trail và quan sát production nâng cao.

Pricing trong MVP là dữ liệu mẫu, chưa phải cam kết thương mại cuối cùng.
