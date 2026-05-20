import type { onMessage, OnClose, onError, OnOpen } from "@/types/types";

export class ChatSocket {
  private socket: WebSocket | null = null;
  private readonly baseWsUrl: string;

  constructor(
    baseWsUrl = process.env.NEXT_PUBLIC_WS_URL ||
      "ws://localhost:3500/api/v1/chat/chat",
  ) {
    this.baseWsUrl = baseWsUrl;
  }

  connect(params: {
    accessToken: string;
    chatToken: string;
    onMessage: onMessage;
    onOpen?: OnOpen;
    onError?: onError;
    onClose?: OnClose;
  }) {
    const { accessToken, chatToken, onMessage, onOpen, onError, onClose } =
      params;

    if (!accessToken) throw new Error("Missing access token");
    if (!chatToken) throw new Error("Missing chat token");

    if (this.socket) this.disconnect();

    const url = new URL(this.baseWsUrl);
    url.searchParams.set("token", accessToken);
    url.searchParams.set("chat_token", chatToken);

    this.socket = new WebSocket(url.toString());

    this.socket.onopen = (event) => {
      if (onOpen) onOpen(event);
    };

    this.socket.onmessage = (event) => {
      onMessage(event.data);
    };

    this.socket.onerror = (event) => {
      if (onError) onError(event);
    };

    this.socket.onclose = (event) => {
      if (onClose) onClose(event);
    };
  }

  send(message: string) {
    if (!this.socket || this.socket.readyState != WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }
    this.socket.send(message);
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  isConnected() {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

export function createChatSocket(params: {
  accessToken: string;
  chatToken: string;
  onMessage: onMessage;
  onOpen?: OnOpen;
  onError?: onError;
  onClose?: OnClose;
}) {
  const ws = new ChatSocket();
  ws.connect(params);
  return ws;
}
