# Interior Quotation Chatbot

Chatbot hỗ trợ sale nội thất (tủ bếp). Bot thu thập thông tin khách theo kịch bản, gửi ảnh
mẫu phù hợp và xuất báo giá tạm tính.

```text
Agent_sale/
├── backend/    # Core: FastAPI + LLM slot extraction + flow engine + báo giá
└── frontend/   # Tùy chọn: web demo React + TypeScript, chỉ gọi REST API của backend
```

Frontend không chứa logic nghiệp vụ. Mọi thứ (kịch bản, memory, chọn ảnh, tính giá) nằm ở
backend, nên có thể thay frontend bằng Zalo/Messenger hay app khác mà không sửa core.

## Luồng xử lý mỗi tin nhắn

```text
Tin nhắn ─► Phân tích (LLM / rule-based) ─► Cập nhật memory (slots)
        ─► Đủ dữ liệu section hiện tại?
             ├─ Đủ      ─► chuyển section tiếp theo ─► ... ─► tính báo giá
             └─ Chưa đủ ─► hỏi lại thông tin thiếu
                            └─ quá max_attempts ─► dùng defaults hoặc chuyển nhân viên
```

LLM **chỉ** trích xuất slot và intent. Việc chuyển section, chọn ảnh và tính giá đều là
code xác định, cấu hình bằng YAML.

## Backend

Yêu cầu Python 3.12.

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
Copy-Item .env.example .env      # điền GEMINI_API_KEY hoặc OPENAI_API_KEY nếu có
uvicorn app.main:app --reload    # http://localhost:8000/docs
```

Test và lint:

```powershell
python -m pytest
ruff check . ; ruff format --check .
```

### Cấu trúc

```text
backend/
├── app/
│   ├── api/             # routes.py, schemas.py — lớp HTTP mỏng
│   ├── application/     # ChatService, FlowEngine, SlotService, QuotationService,
│   │                    # ImageAssetSkill, ResponseService, ports (interfaces)
│   ├── domain/          # model và enum nghiệp vụ thuần
│   ├── infrastructure/  # extractors (gemini/openai/rule_based/fallback), YAML repos,
│   │                    # in-memory session store, keyword asset matcher
│   ├── prompts/         # system prompt cho LLM extractor
│   ├── container.py     # nối dependency
│   ├── settings.py
│   └── main.py
├── config/
│   ├── flow.yaml        # kịch bản: lời chào, nhãn câu hỏi, các section
│   └── pricing.yaml     # hạng mục, vật liệu, đơn giá
├── assets/
│   ├── assets.yaml      # metadata ảnh (intent, keyword, câu giới thiệu)
│   └── images/
└── tests/
```

### API

| Method | Path | Mô tả |
|---|---|---|
| GET | `/health` | Trạng thái và extractor đang dùng |
| POST | `/api/v1/sessions` | Tạo phiên, trả lời chào trong `message_history` |
| GET | `/api/v1/sessions/{id}` | Xem toàn bộ state của phiên |
| POST | `/api/v1/chat` | `{session_id?, message}` → reply, slots, quote, assets |
| GET | `/api/v1/assets/{id}/image` | File ảnh của asset |

`assets[].url` trong response là đường dẫn tương đối so với API root.

### Chọn LLM

`SLOT_EXTRACTOR` trong `backend/.env`: `auto` | `gemini` | `openai` | `rule_based`.

- `auto` dùng OpenAI nếu có key + model, sau đó Gemini, cuối cùng là rule-based.
- Provider thiếu key/model sẽ bị bỏ qua; nếu provider lỗi khi đang chạy (timeout, quota…),
  lượt đó tự dùng rule-based extractor.
- Danh sách mã vật liệu trong prompt được sinh từ `pricing.yaml`.

### Tùy biến không cần sửa code

- **Kịch bản** — `config/flow.yaml`. Mỗi section có `required_slots`, `optional_slots`,
  `max_attempts`, `failure_policy` (`needs_human` hoặc `use_defaults` + `defaults`),
  `suggested_assets`. Section có `kind: quote` là bước tính báo giá.
  `use_defaults` chỉ áp dụng sau khi khách trả lời hụt `max_attempts` lần.
- **Bảng giá** — `config/pricing.yaml`. `line_items` khai báo tên hạng mục, slot chiều dài
  riêng (`length_slot`) và slot cho phép bỏ hạng mục (`toggle_slot`). Hạng mục thiếu
  chiều dài riêng dùng `kitchen_length_m` và được ghi vào giả định của báo giá.
- **Ảnh** — thêm file vào `assets/images/` và một record trong `assets/assets.yaml`.

Slot mới cần thêm normalize/validate trong `SlotService` và cho extractor nhận diện.

## Frontend (demo, tùy chọn)

Yêu cầu Node.js 20+. Chạy backend trước, sau đó:

```powershell
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Vite proxy `/api` và `/health` sang `http://localhost:8000`, nên không cần cấu hình CORS
khi dev. Nếu frontend được host riêng, đặt `VITE_API_URL=https://backend-host` khi build và
thêm origin đó vào `CORS_ORIGINS` của backend.

```text
frontend/src/
├── api.ts            # client REST có kiểu
├── types.ts          # kiểu TypeScript khớp với backend/app/api/schemas.py
├── App.tsx           # khung chat + quản lý phiên
└── components/       # MessageBubble, QuoteCard, StatePanel
```

## Chưa triển khai

- Lưu phiên bền vững (Redis/PostgreSQL) và locking đa process; hiện session nằm trong RAM.
- Đồng bộ bảng giá từ Google Sheets.
- Truyền ngữ cảnh câu hỏi đang hỏi cho extractor (ví dụ khách chỉ trả lời "4").
- Auth, Messenger/Zalo, sinh PDF báo giá.

Pricing trong repo là dữ liệu mẫu, chưa phải cam kết thương mại.
