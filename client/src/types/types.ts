import type { FormEvent } from "react";

export type ConnectionState =
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";

export type OnMessage = (message: string) => void;
export type OnError = (message: Event) => void;
export type OnClose = (event: CloseEvent) => void;
export type OnOpen = (event: Event) => void;

export type AuthResponse = {
  access_token: string;
  token_type: string;
  user: {
    id: string;
    name: string;
    email: string;
  };
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
};

export type ChatInterfaceProps = {
  displayName: string;
  connectionState: ConnectionState;
  messages: ChatMessage[];
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  isAssistantTyping: boolean;
};

export type ChatPanelProps = {
  displayName: string;
};

export interface ChatSession {
  id: string;
  title: string;
  preview: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface ChatSidebarProps {
  activeSessionId: string | null;
  onSelectSession: (session: ChatSession) => void;
  onNewChat: () => void;
  onDeleteSession?: (id: string) => void;
  liveMessages?: ChatMessage[];
}

export type RedisHistoryMessage = {
  id?: string;
  msg?: string;
};

export type ChatSessionResponse = {
  token: string;
  messages?: RedisHistoryMessage[];
};

export type StoredAuthUser = {
  id: string;
  name: string;
  email: string;
};

export type ToastTone = "info" | "success" | "warning" | "error";

export type ToastPayload = {
  title: string;
  description?: string;
  tone?: ToastTone;
};

export type ToastItem = ToastPayload & {
  id: string;
  tone: ToastTone;
};

export type RateLimitResponse = {
  detail?: string;
  rate_limit?: {
    scope?: string;
    retry_after?: number;
  };
};
