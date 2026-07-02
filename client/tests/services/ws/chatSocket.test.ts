import { createChatSocket } from "@/services/ws/chatSocket";

class MockWebSocket {
  url: string;
  onopen: (() => void) | null = null;
  onclose: (() => void) | null = null;
  onerror: ((error: any) => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;

  send = jest.fn();
  close = jest.fn();

  constructor(url: string) {
    this.url = url;
  }
}

describe("Chat Socket Service", () => {
  let originalWebSocket: any;
  let mockParams: any;

  beforeEach(() => {
    originalWebSocket = global.WebSocket;
    global.WebSocket = MockWebSocket as any;

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
    global.WebSocket = originalWebSocket;
    jest.clearAllMocks();
  });

  it("Happy Path: successfully initializes and formats the connection URL", () => {
    const socketWrapper = createChatSocket(mockParams);

    const wsInstance = (socketWrapper as any).socket as MockWebSocket;

    expect(wsInstance.url).toContain("chat_token=test-chat-token");
    expect(wsInstance.url).toContain("ws_ticket=test-ws-ticket");

    expect(wsInstance.url).toContain("ws://localhost:3501/api/v1/chat/chat");
  });

  it("Happy Path: correctly maps native WebSocket events to our custom callbacks", () => {
    createChatSocket(mockParams);
    const wsInstance =
      (global.WebSocket as any).mock?.instances[0] ||
      Object.values(mockParams)[0];

    const socketWrapper = createChatSocket(mockParams);
    const socket = (socketWrapper as any).socket as MockWebSocket;

    socket.onopen!();
    expect(mockParams.onOpen).toHaveBeenCalledTimes(1);

    socket.onmessage!({ data: "Hello from server" });
    expect(mockParams.onMessage).toHaveBeenCalledWith("Hello from server");

    socket.onclose!();
    expect(mockParams.onClose).toHaveBeenCalledTimes(1);

    socket.onerror!(new Error("Socket error"));
    expect(mockParams.onError).toHaveBeenCalledTimes(1);
  });

  it("Happy Path: sendMessage stringifies the payload and sends it via the native socket", () => {
    const socketWrapper = createChatSocket(mockParams);
    const wsInstance = (socketWrapper as any).socket as MockWebSocket;

    socketWrapper.sendMessage("Hello AI");

    expect(wsInstance.send).toHaveBeenCalledWith(
      JSON.stringify({ message: "Hello AI" }),
    );
  });

  it("Happy Path: disconnect explicitly closes the native socket", () => {
    const socketWrapper = createChatSocket(mockParams);
    const wsInstance = (socketWrapper as any).socket as MockWebSocket;

    socketWrapper.disconnect();

    expect(wsInstance.close).toHaveBeenCalledTimes(1);
  });
});
