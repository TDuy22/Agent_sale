import { type FormEvent, useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api } from "./api";
import { MessageBubble, type UiMessage } from "./components/MessageBubble";
import { type ConversationSnapshot, StatePanel } from "./components/StatePanel";
import type { SessionResponse } from "./types";

// Remembers the session across reloads (e.g. when the browser discards a background tab).
const SESSION_KEY = "interior-quote.session-id";

const storage = {
  get: () => {
    try {
      return localStorage.getItem(SESSION_KEY);
    } catch {
      return null;
    }
  },
  set: (sessionId: string) => {
    try {
      localStorage.setItem(SESSION_KEY, sessionId);
    } catch {
      // Storage may be blocked; the chat still works, it just won't survive a reload.
    }
  },
};

function snapshotFromSession(session: SessionResponse): ConversationSnapshot {
  return {
    status: session.status,
    currentSection: session.current_section,
    completedSections: session.completed_sections,
    slots: session.slots,
    missingSlots: session.missing_slots ?? [],
  };
}

function messagesFromSession(session: SessionResponse): UiMessage[] {
  const messages: UiMessage[] = session.message_history.map(({ role, content, assets }) => ({
    role,
    content,
    assets: assets ?? [],
  }));
  // The current quote belongs to the latest assistant reply.
  const last = messages.findLastIndex((message) => message.role === "assistant");
  if (session.quote && last >= 0) messages[last] = { ...messages[last], quote: session.quote };
  return messages;
}

async function restoreOrCreateSession(forceNew: boolean): Promise<SessionResponse> {
  const storedId = forceNew ? null : storage.get();
  if (storedId) {
    try {
      return await api.getSession(storedId);
    } catch {
      // Unknown session (e.g. the backend restarted): start a new one.
    }
  }
  const session = await api.createSession();
  storage.set(session.session_id);
  return session;
}

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<UiMessage[]>([]);
  const [snapshot, setSnapshot] = useState<ConversationSnapshot | null>(null);
  const [extractor, setExtractor] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [pending, setPending] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const initialized = useRef(false);

  const append = (message: UiMessage) => setMessages((current) => [...current, message]);

  const loadSession = useCallback(async (forceNew: boolean) => {
    try {
      const session = await restoreOrCreateSession(forceNew);
      setSessionId(session.session_id);
      setMessages(messagesFromSession(session));
      setSnapshot(snapshotFromSession(session));
    } catch (error) {
      setMessages([{ role: "assistant", content: `Không kết nối được backend: ${error}`, error: true }]);
    }
  }, []);

  useEffect(() => {
    // StrictMode runs effects twice in dev; only load the session once.
    if (initialized.current) return;
    initialized.current = true;
    void loadSession(false);
    api
      .health()
      .then((health) => setExtractor(health.extractor))
      .catch(() => setExtractor(null));
  }, [loadSession]);

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
      if (error instanceof ApiError && error.status === 404) {
        // Sessions live in backend RAM, so a backend restart drops them: start over.
        await loadSession(true);
        setInput(text);
        append({
          role: "assistant",
          content: "Phiên cũ không còn trên máy chủ (backend đã khởi động lại). Đã tạo phiên mới, vui lòng gửi lại tin nhắn.",
          error: true,
        });
        return;
      }
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

      <StatePanel snapshot={snapshot} extractor={extractor} onReset={() => void loadSession(true)} />
    </div>
  );
}
