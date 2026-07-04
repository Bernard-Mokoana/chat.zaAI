import { renderHook, act, waitFor } from "@testing-library/react";
import { useWebSocketChat } from "@/hooks/useWebSocketChat";
import type { ChatSocket } from "@/services/ws/chatSocket";
import { createChatSocket } from "@/services/ws/chatSocket";
import { getAccessToken } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import { createWebsocketTicket } from "@/services/chat/chatApi";

jest.mock("@/services/ws/chatSocket");
jest.mock("@/services/storage/chatStorage");
jest.mock("@/services/toast/toastEvents");
jest.mock("@/services/chat/chatApi");

describe("useWebSocketChat Hook", () => {
  type MockSocket = Pick<ChatSocket, "disconnect">;

  let mockSocketInstance: MockSocket;

  beforeEach(() => {
    jest.clearAllMocks();

    mockSocketInstance = { disconnect: jest.fn() };
    (createChatSocket as jest.MockedFunction<typeof createChatSocket>).mockReturnValue(
      mockSocketInstance as ChatSocket,
    );
    (createWebsocketTicket as jest.MockedFunction<typeof createWebsocketTicket>).mockResolvedValue(
      { ws_ticket: "ticket-123" },
    );
  });

  it("Error Condition: fails to connect if access token is missing", () => {
    (getAccessToken as jest.Mock).mockReturnValue(null);
    const mockOnMessage = jest.fn();

    const { result } = renderHook(() => useWebSocketChat());

    act(() => {
      result.current.connect("chat-token-123", mockOnMessage);
    });

    expect(result.current.connectionState).toBe("error");
    expect(showToast).toHaveBeenCalledWith(
      expect.objectContaining({ tone: "error" }),
    );
    expect(createChatSocket).not.toHaveBeenCalled();
  });

  it("Happy Path: successfully initializes socket connection parameters", async () => {
    (getAccessToken as jest.Mock).mockReturnValue("valid-access-token");
    const mockOnMessage = jest.fn();

    const { result } = renderHook(() => useWebSocketChat());

    act(() => {
      result.current.connect("chat-token-123", mockOnMessage);
    });

    await waitFor(() => expect(createChatSocket).toHaveBeenCalledTimes(1));

    const socketParams = (
      createChatSocket as jest.MockedFunction<typeof createChatSocket>
    ).mock.calls[0][0];
    expect(createWebsocketTicket).toHaveBeenCalledWith("chat-token-123");
    expect(socketParams.wsTicket).toBe("ticket-123");
    expect(socketParams.chatToken).toBe("chat-token-123");

    act(() => socketParams.onOpen?.(new Event("open")));
    expect(result.current.connectionState).toBe("connected");
    expect(result.current.isConnected).toBe(true);

    socketParams.onMessage("Hello world");
    expect(mockOnMessage).toHaveBeenCalledWith("Hello world");

    socketParams.onMessage("Too many messages. Please wait.");
    expect(showToast).toHaveBeenCalledWith(
      expect.objectContaining({
        tone: "warning",
        title: "Message limit reached",
      }),
    );

    act(() => socketParams.onError?.(new Event("error")));
    expect(result.current.connectionState).toBe("error");
  });

  it("Happy Path: explicitly disconnecting updates state and drops the socket", async () => {
    (getAccessToken as jest.Mock).mockReturnValue("valid-access-token");
    const { result } = renderHook(() => useWebSocketChat());

    act(() => {
      result.current.connect("chat-token-123", jest.fn());
    });

    await waitFor(() => expect(createChatSocket).toHaveBeenCalledTimes(1));

    act(() => {
      result.current.disconnect();
    });

    expect(mockSocketInstance.disconnect).toHaveBeenCalledTimes(1);
    expect(result.current.connectionState).toBe("disconnected");
  });
});
