# Interior Quotation Chatbot

Base project cho chatbot tư vấn và báo giá tủ bếp theo finite-state workflow. MVP chạy
hoàn toàn bằng rule-based slot extractor, không cần API key, đồng thời giữ một adapter
OpenAI structured output tùy chọn.

## Kiến trúc

```text
HTTP / CLI
    -> ChatService
        -> SlotExtractor (rule-based hoặc OpenAI)
        -> FlowEngine (đọc config/flow.yaml)
        -> SlotService (normalize, validate, merge memory)
        -> QuotationService (Decimal/integer VND, không gọi LLM)
        -> ConversationRepository
```

- `app/domain`: model và enum nghiệp vụ, không biết FastAPI hay Google Sheets.
- `app/application`: orchestration, workflow, slot validation, quotation và ports.
- `app/infrastructure`: YAML loaders, memory repository, extractor adapters.
- `app/api`: request/response schema và route mỏng.
- `config`: flow, pricing và asset metadata có thể thay độc lập.
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

## Test và lint

```powershell
python -m pytest
ruff check .
ruff format --check .
```

## Thay đổi flow

Sửa `config/flow.yaml`; `FlowEngine` duyệt danh sách section theo thứ tự và không chứa
chuỗi `if/else` theo từng kịch bản. Mỗi section khai báo `required_slots`,
`optional_slots`, `max_attempts`, `failure_policy` và tùy chọn `defaults`.

Khi thêm required slot mới:

1. Thêm slot vào YAML.
2. Bổ sung normalize/validation tương ứng trong `SlotService`.
3. Cho extractor trả slot đó.
4. Thêm nhãn câu hỏi trong `ResponseService` và test luồng.

`failed_attempt_count` chỉ tăng khi người dùng không cung cấp slot hợp lệ đang được hỏi;
`turn_count` vẫn ghi tổng số lượt dừng tại section.

## Thêm vật liệu và đơn giá

Thêm material code trong `config/pricing.yaml`, gồm `name` và giá integer VND cho các
code line item. Sau đó bổ sung alias nhận diện trong rule-based extractor hoặc để OpenAI
extractor trả đúng code. Request không đọc Google Sheets; YAML được load một lần khi tạo
service.

Nếu chỉ có `kitchen_length_m`, MVP dùng chiều dài này cho tủ dưới, tủ trên, mặt đá, ốp
bếp và LED. Quote luôn ghi rõ giả định đó. Chiều dài riêng, nếu có, được ưu tiên.

## Thay memory repository

Tạo adapter mới implement `ConversationRepository` trong `app/application/ports.py`
(ví dụ Redis/PostgreSQL), rồi thay adapter tại `app/container.py`. Domain và FlowEngine
không cần sửa. Adapter production cần bổ sung atomic update/concurrency control.

## Bật OpenAI extractor

Trong `.env`:

```dotenv
SLOT_EXTRACTOR=openai
OPENAI_API_KEY=...
OPENAI_MODEL=...
```

Model name không được hardcode. Adapter dùng Pydantic structured output qua Responses
API; LLM chỉ trích xuất slot, không chuyển section và không tính giá. Nếu thiếu key hoặc
model, ứng dụng log cảnh báo rồi tự động dùng rule-based extractor. Cách gọi bám theo
[tài liệu Structured Outputs chính thức của OpenAI](https://developers.openai.com/api/docs/guides/structured-outputs).

## Chưa triển khai

- Đồng bộ Google Sheets/OAuth; `scripts/import_pricing_sheet.py` chỉ là skeleton.
- Database/Redis persistence và locking đa process.
- Frontend, auth production, Messenger/Zalo.
- OCR/bản vẽ, RAG/vector database.
- Sinh PDF/ảnh và upload asset thật.
- Admin UI, audit trail và quan sát production nâng cao.

Pricing trong MVP là dữ liệu mẫu, chưa phải cam kết thương mại cuối cùng.
