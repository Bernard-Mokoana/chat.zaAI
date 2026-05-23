const CHAT_TOKEN_KEY = "chat_token";
const CHAT_MESSAGES_KEY = "chat_messages";
const CHAT_NAME = "chat_name";
const ACCESS_TOKEN_KEY = "access_token";

export function getChatToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(CHAT_TOKEN_KEY);
}

export function setChatToken(token: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(CHAT_TOKEN_KEY, token);
}

export function clearChatToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CHAT_TOKEN_KEY);
}

export function getChatMessages<T = unknown[]>(): T | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(CHAT_MESSAGES_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as T;
  } catch (error) {
    console.warn("Failed to parse chat messages from storage", error);
    return null;
  }
}

export function setChatMessages(messages: unknown[]) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(CHAT_MESSAGES_KEY, JSON.stringify(messages));
  } catch (error) {
    console.warn("Failed to save chat messages to storage", error);
  }
}

export function clearChatMessages() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CHAT_MESSAGES_KEY);
}

export function getChatName() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(CHAT_NAME);
}

export function setChatName(name: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(CHAT_NAME, name);
}

export function clearChatName() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(CHAT_NAME);
}

export function getAccessToken() {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(ACCESS_TOKEN_KEY);
}

export function setAccessToken(token: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken() {
  if (typeof window === "undefined") return;
  localStorage.removeItem(ACCESS_TOKEN_KEY);
}
