import type { FormEvent, ReactNode } from "react";

/**
 * Connection state for WebSocket connections
 */
export type ConnectionState =
  | "connecting"
  | "connected"
  | "disconnected"
  | "error";

/**
 * WebSocket event handlers
 */
export type OnMessage = (message: string) => void;
export type OnError = (message: Event) => void;
export type OnClose = (event: CloseEvent) => void;
export type OnOpen = (event: Event) => void;

/**
 * Authentication types
 */
export interface AuthUser {
  id: string;
  name: string;
  email: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: AuthUser;
}

export interface StoredAuthUser extends AuthUser {}

export interface LoginPayload {
  email: string;
  password: string;
}

export interface RegisterPayload {
  name: string;
  email: string;
  password: string;
}

export interface ForgotPasswordPayload {
  email: string;
}

export interface ResetPasswordPayload {
  token: string;
  new_password: string;
}

export type AuthAction = "login" | "register";

export interface ApiErrorPayload {
  detail?: string;
}

export interface GenericAuthResponse {
  message: string;
}

export interface PasswordResetState {
  newPassword: string;
  confirmPassword: string;
  isPending: boolean;
  errorMessage: string;
  validationErrors: Array<{ field: string; message: string }>;
}

/**
 * Chat message types
 */
export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
}

export interface RedisHistoryMessage {
  id?: string;
  msg?: string;
  role?: string;
}

export interface ChatSession {
  id: string;
  chatToken?: string;
  title: string;
  preview: string;
  messages: ChatMessage[];
  createdAt: number;
  updatedAt: number;
}

export interface ChatSessionResponse {
  token: string;
  messages?: RedisHistoryMessage[];
}

export interface ChatHistoryResponse {
  status: string;
  history: RedisHistoryMessage[];
}

/**
 * API Response types
 */
export interface ApiErrorResponse {
  detail?: unknown;
}

export interface RateLimitResponse extends ApiErrorResponse {
  rate_limit?: {
    scope?: string;
    retry_after?: number;
  };
}

/**
 * Toast notification types
 */
export type ToastTone = "info" | "success" | "warning" | "error";

export interface ToastPayload {
  title: string;
  description?: string;
  tone?: ToastTone;
}

export interface ToastItem extends ToastPayload {
  id: string;
  tone: ToastTone;
}

/**
 * Form validation types
 */
export interface ValidationError {
  field: string;
  message: string;
}

export interface FormValidationResult {
  isValid: boolean;
  errors: ValidationError[];
}

/**
 * Component props types
 */
export interface ChatInterfaceProps {
  displayName: string;
  chatToken: string | null;
  connectionState: ConnectionState;
  messages: ChatMessage[];
  input: string;
  onInputChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  isAssistantTyping: boolean;
}

export interface ChatPanelProps {
  displayName: string;
}

export interface ChatSidebarProps {
  activeSessionId: string | null;
  onSelectSession: (session: ChatSession) => void;
  onNewChat: () => void;
  onDeleteSession?: (id: string) => void;
  liveMessages?: ChatMessage[];
  refreshTrigger?: number;
}
export interface FormFieldProps extends Omit<
  React.InputHTMLAttributes<HTMLInputElement>,
  "id"
> {
  label: string;
  id: string;
  error?: string;
}

export interface AlertBannerProps {
  tone: ToastTone;
  message: string;
  onDismiss?: () => void;
}

/**
 * Type guards
 */
export const isConnectionState = (value: unknown): value is ConnectionState => {
  return (
    value === "connecting" ||
    value === "connected" ||
    value === "disconnected" ||
    value === "error"
  );
};

export const isToastTone = (value: unknown): value is ToastTone => {
  return (
    value === "info" ||
    value === "success" ||
    value === "warning" ||
    value === "error"
  );
};

export const isChatMessage = (value: unknown): value is ChatMessage => {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "role" in value &&
    "content" in value &&
    typeof (value as ChatMessage).id === "string" &&
    typeof (value as ChatMessage).content === "string" &&
    ((value as ChatMessage).role === "user" ||
      (value as ChatMessage).role === "assistant")
  );
};

export type VerificationStatus = "verifying" | "success" | "error";

export interface VerificationState {
  status: VerificationStatus;
  errorMessage: string;
}

export type AlertTone = "success" | "error" | "info" | "warning";

export interface AuthLayoutProps {
  title: string;
  subtitle?: string;
  children: ReactNode;
  footerLink?: {
    href: string;
    label: string;
  };
}

export interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error) => ReactNode;
}

export interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export interface ModalProps {
  isOpen: boolean;
  title: string;
  description?: string;
  children?: ReactNode;
  onClose: () => void;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
  isDangerous?: boolean;
}

export interface ChatHeaderProps {
  displayName: string;
  connectionState: ConnectionState;
  onLogout: () => void;
}

export interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (event: FormEvent<HTMLFormElement>) => void;
  disabled?: boolean;
  placeholder?: string;
}

export interface ChatMessageListProps {
  messages: ChatMessage[];
  connectionState: ConnectionState;
  isAssistantTyping: boolean;
}

export interface UseChatSessionReturn {
  activeChatToken: string | null;
  messages: ChatMessage[];
  input: string;
  isAssistantTyping: boolean;
  setInput: (value: string) => void;
  setMessages: (messages: ChatMessage[]) => void;
  setIsAssistantTyping: (value: boolean) => void;
  startNewSession: (displayName: string) => Promise<string>;
  loadSessionHistory: (
    token: string,
  ) => Promise<{ messages: ChatMessage[]; success: boolean }>;
  addMessage: (message: ChatMessage) => void;
  clearAllMessages: () => void;
}

export interface UseSessionEventsParams {
  onLoadSession: (
    session: ChatSession,
    messages: ChatMessage[],
  ) => Promise<void>;
  onNewSession: () => Promise<void>;
}

export interface UseWebSocketChatReturn {
  connectionState: ConnectionState;
  isConnected: boolean;
  connect: (chatToken: string, onMessage: (msg: string) => void) => void;
  disconnect: () => void;
}

export interface ChatSocketParams {
  wsTicket: string;
  chatToken: string;
  onMessage: OnMessage;
  onOpen?: OnOpen;
  onError?: OnError;
  onClose?: OnClose;
}
