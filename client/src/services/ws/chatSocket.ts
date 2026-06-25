import type { ChatSocketParams } from "@/types/types";

export class ChatSocket {
  private socket: WebSocket | null = null;
  private readonly baseWsUrl: string;

  constructor(
    baseWsUrl: string = process.env.NEXT_PUBLIC_WS_URL ||
      "ws://localhost:3501/api/v1/chat/chat",
  ) {
    this.baseWsUrl = baseWsUrl;
  }

  connect(params: ChatSocketParams): void {
    const { accessToken, chatToken, onMessage, onOpen, onError, onClose } =
      params;

    if (!accessToken) throw new Error("Missing access token");
    if (!chatToken) throw new Error("Missing chat token");

    if (this.socket) this.disconnect();

    const url = new URL(this.baseWsUrl);
    url.searchParams.set("token", accessToken);
    url.searchParams.set("chat_token", chatToken);

    this.socket = new WebSocket(url.toString());

    this.socket.onopen = (event: Event) => {
      if (onOpen) onOpen(event);
    };

    this.socket.onmessage = (event: MessageEvent) => {
      if (typeof event.data === "string") {
        onMessage(event.data);
      } else {
        console.error("Received non-text websocket message:", event.data);
      }
    };

    this.socket.onerror = (event: Event) => {
      if (onError) onError(event);
    };

    this.socket.onclose = (event: CloseEvent) => {
      if (onClose) onClose(event);
    };
  }

  sendMessage(message: string): void {
    if (!this.socket || this.socket.readyState !== WebSocket.OPEN) {
      throw new Error("WebSocket is not connected");
    }
    this.socket.send(JSON.stringify({ message }));
  }

  disconnect(): void {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
  }

  isConnected(): boolean {
    return this.socket?.readyState === WebSocket.OPEN;
  }
}

export function createChatSocket(params: ChatSocketParams): ChatSocket {
  const ws = new ChatSocket();
  ws.connect(params);
  return ws;
}
