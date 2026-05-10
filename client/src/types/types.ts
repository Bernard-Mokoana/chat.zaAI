import type { FormEvent } from "react";

type ConnectionState = "connecting" | "connected" | "disconnected" | "error";

export type onMessage = (message: string) => void;
export type onError = (message: Event) => void;
export type OnClose = (event: CloseEvent) => void;
export type OnOpen = (event: Event) => void;

export type MessageHandler = (message: string) => void;
export type ErrorHandler = (event: Event) => void;

export type AuthResponse = {
  access_token: string;
  token_type: string;
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
