import type { ChatResponse, HealthResponse, SessionResponse } from "./types";

// Empty by default: the Vite dev server proxies /api to the backend.
const API_URL = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.detail ?? `HTTP ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export const assetUrl = (path: string) => `${API_URL}${path}`;

export const api = {
  health: () => request<HealthResponse>("/health"),
  createSession: () => request<SessionResponse>("/api/v1/sessions", { method: "POST" }),
  chat: (sessionId: string, message: string) =>
    request<ChatResponse>("/api/v1/chat", {
      method: "POST",
      body: JSON.stringify({ session_id: sessionId, message }),
    }),
};
