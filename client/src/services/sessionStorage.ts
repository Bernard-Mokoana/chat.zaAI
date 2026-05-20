import { ChatSession, ChatMessage } from "@/types/types";

const SESSIONS_KEY = "chat_sessions";
const ACTIVE_SESSION_KEY = "active_session_id";

export function loadSessions(): ChatSession[] {
  try {
    const parsed = JSON.parse(localStorage.getItem(SESSIONS_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function saveSession(session: ChatSession): void {
  try {
    const sessions = loadSessions();
    const idx = sessions.findIndex((s) => s.id === session.id);
    if (idx >= 0) sessions[idx] = session;
    else sessions.unshift(session);
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  } catch (error) {
    console.error("Failed to save session:", error);
  }
}

export function deleteSession(id: string): void {
  try {
    const sessions = loadSessions().filter((s) => s.id !== id);
    localStorage.setItem(SESSIONS_KEY, JSON.stringify(sessions));
  } catch (error) {
    console.error("Failed to delete session:", error);
  }
}

export function getActiveSessionId(): string | null {
  try {
    return localStorage.getItem(ACTIVE_SESSION_KEY);
  } catch {
    return null;
  }
}

export function setActiveSessionId(id: string | null): void {
  try {
    if (id) localStorage.setItem(ACTIVE_SESSION_KEY, id);
    else localStorage.removeItem(ACTIVE_SESSION_KEY);
  } catch (error) {
    console.error("Failed to set active session", error);
  }
}

export function createSession(firstMessage?: ChatMessage): ChatSession {
  const now = Date.now();
  const title = firstMessage
    ? firstMessage.content.slice(0, 40) +
      (firstMessage.content.length > 40 ? "…" : "")
    : "New conversation";
  return {
    id: `session_${now}_${Math.random().toString(36).slice(2, 7)}`,
    title,
    preview: firstMessage?.content ?? "",
    messages: firstMessage ? [firstMessage] : [],
    createdAt: now,
    updatedAt: now,
  };
}
