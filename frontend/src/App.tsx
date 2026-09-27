import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { api } from "./api";
import { MessageBubble, type UiMessage } from "./components/MessageBubble";
import { type ConversationSnapshot, StatePanel } from "./components/StatePanel";
import type { SessionResponse } from "./types";

function snapshotFromSession(session: SessionResponse): ConversationSnapshot {
  return {
    status: session.status,
    currentSection: session.current_section,
    completedSections: session.completed_sections,
    slots: session.slots,
    missingSlots: [],
  };
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [snapshot, setSnapshot] = useState<ConversationSnapshot | null>(null);
  const [extractor, setExtractor] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const append = (message: UiMessage) => setMessages((current) => [...current, message]);

  const startSession = useCallback(async () => {
    try {
      const session = await api.createSession();
      setSessionId(session.session_id);
      setMessages(session.message_history.map(({ role, content }) => ({ role, content })));
      setSnapshot(snapshotFromSession(session));
    } catch (error) {
      setMessages([{ role: "assistant", content: `Không kết nối được backend: ${error}`, error: true }]);
    }
  }, []);

  useEffect(() => {
    void startSession();
    api
      .health()
      .then((health) => setExtractor(health.extractor))
      .catch(() => setExtractor(null));
  }, [startSession]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, pending]);

  async function send(event: FormEvent) {
    event.preventDefault();
    const text = input.trim();
    if (!text || !sessionId || pending) return;

    setInput("");
    append({ role: "user", content: text });
    setPending(true);
    try {
      const result = await api.chat(sessionId, text);
      append({ role: "assistant", content: result.reply, assets: result.assets, quote: result.quote });
      setSnapshot({
        status: result.status,
        currentSection: result.current_section,
        completedSections: result.completed_sections,
        slots: result.collected_slots,
        missingSlots: result.missing_slots,
      });
    } catch (error) {
      append({ role: "assistant", content: `Có lỗi khi gửi tin nhắn: ${error}`, error: true });
    } finally {
      setPending(false);
    }
  }

  return (
    <div className="layout">
      <header>
        <h1>AI Sales Agent — Tư vấn tủ bếp</h1>
        <p className="muted">Demo: phân tích tin nhắn → memory → gửi ảnh → báo giá</p>
      </header>

      <main className="chat">
        <div className="messages">
          {messages.map((message, index) => (
            <MessageBubble key={index} message={message} />
          ))}
          {pending && <div className="message assistant typing">Đang phân tích…</div>}
          <div ref={bottomRef} />
        </div>
        <form className="composer" onSubmit={send}>
          <input
            value={input}
            onChange={(event) => setInput(event.target.value)}
            placeholder="Nhập nhu cầu của khách…"
            disabled={!sessionId}
            autoFocus
          />
          <button type="submit" disabled={!sessionId || pending || !input.trim()}>
            Gửi
          </button>
        </form>
      </main>

      <StatePanel snapshot={snapshot} extractor={extractor} onReset={startSession} />
    </div>
  );
}
