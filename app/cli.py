import json

from app.container import build_chat_service


def main() -> None:
    """Run an interactive local conversation without an API key."""

    service = build_chat_service()
    state = service.create_session()
    print("Chatbot báo giá nội thất. Lệnh: /state, /reset, /quit")
    while True:
        try:
            message = input("Bạn: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not message:
            continue
        if message == "/quit":
            break
        if message == "/reset":
            state = service.create_session()
            print(f"Đã tạo phiên mới: {state.session_id}")
            continue
        if message == "/state":
            current = service.get_session(state.session_id)
            print(json.dumps(current.model_dump(mode="json"), ensure_ascii=False, indent=2))
            continue
        result = service.chat(message, state.session_id)
        print(f"Agent: {result.reply}")


if __name__ == "__main__":
    main()
