import { createChatSocket } from "@/services/ws/chatSocket";
import type { ChatSocketParams } from "@/types/types";

class MockWebSocket {
  static readonly OPEN = 1;
  static instances: MockWebSocket[] = [];

  url: string;
  readyState = MockWebSocket.OPEN;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onerror: ((error: Event) => void) | null = null;
  onmessage: ((event: MessageEvent<string>) => void) | null = null;

  send = jest.fn();
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }
}

describe("Chat Socket Service", () => {
  type ChatSocketTestInstance = {
    socket: MockWebSocket | null;
    sendMessage: (message: string) => void;
    disconnect: () => void;
  };

  let originalWebSocket: typeof WebSocket;
  let mockParams: ChatSocketParams;

  beforeEach(() => {
    originalWebSocket = globalThis.WebSocket;
    globalThis.WebSocket = MockWebSocket as unknown as typeof WebSocket;
    MockWebSocket.instances = [];

    mockParams = {
      wsTicket: "test-ws-ticket",
      chatToken: "test-chat-token",
      onOpen: jest.fn(),
      onClose: jest.fn(),
      onError: jest.fn(),
      onMessage: jest.fn(),
    };
  });

  afterEach(() => {
    globalThis.WebSocket = originalWebSocket;
    jest.clearAllMocks();
  });

  it("Happy Path: successfully initializes and formats the connection URL", () => {
    const socketWrapper = createChatSocket(mockParams);
    const wsInstance = MockWebSocket.instances[0];
    const typedSocket = socketWrapper as unknown as ChatSocketTestInstance;

    expect(wsInstance.url).toContain("chat_token=test-chat-token");
    expect(wsInstance.url).toContain("ws_ticket=test-ws-ticket");

    expect(wsInstance.url).toContain("ws://localhost:3501/api/v1/chat/chat");
    expect(typedSocket.socket).toBe(wsInstance);
  });

  it("Happy Path: correctly maps native WebSocket events to our custom callbacks", () => {
    const socketWrapper = createChatSocket(mockParams);
    const wsInstance = MockWebSocket.instances[0];
    const socket = socketWrapper as unknown as ChatSocketTestInstance;
    expect(socket.socket).toBe(wsInstance);

    wsInstance.onopen?.(new Event("open"));
    expect(mockParams.onOpen).toHaveBeenCalledTimes(1);

    wsInstance.onmessage?.(
      new MessageEvent("message", { data: "Hello from server" }),
    );
    expect(mockParams.onMessage).toHaveBeenCalledWith("Hello from server");

    wsInstance.onclose?.(new CloseEvent("close"));
    expect(mockParams.onClose).toHaveBeenCalledTimes(1);

    wsInstance.onerror?.(new Event("error"));
    expect(mockParams.onError).toHaveBeenCalledTimes(1);
  });

  it("Happy Path: sendMessage stringifies the payload and sends it via the native socket", () => {
    const socketWrapper = createChatSocket(mockParams);
    const wsInstance = MockWebSocket.instances[0];

    socketWrapper.sendMessage("Hello AI");

    expect(wsInstance.send).toHaveBeenCalledWith(
      JSON.stringify({ message: "Hello AI" }),
    );
  });

  it("Happy Path: disconnect explicitly closes the native socket", () => {
    const socketWrapper = createChatSocket(mockParams);
    const wsInstance = MockWebSocket.instances[0];

    socketWrapper.disconnect();

    expect(wsInstance.close).toHaveBeenCalledTimes(1);
  });
});
