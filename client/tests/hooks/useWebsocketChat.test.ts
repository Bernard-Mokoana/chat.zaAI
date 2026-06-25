import { renderHook, act } from "@testing-library/react";
import { useWebSocketChat } from "@/hooks/useWebSocketChat";
import { createChatSocket } from "@/services/ws/chatSocket";
import { getAccessToken } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";

jest.mock("@/services/ws/chatSocket");
jest.mock("@/services/storage/chatStorage");
jest.mock("@/services/toast/toastEvents");

describe("useWebSocketChat Hook", () => {
  let mockSocketInstance: any;

  beforeEach(() => {
    jest.clearAllMocks();

    mockSocketInstance = { disconnect: jest.fn() };
    (createChatSocket as jest.Mock).mockReturnValue(mockSocketInstance);
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

  it("Happy Path: successfully initializes socket connection parameters", () => {
    (getAccessToken as jest.Mock).mockReturnValue("valid-access-token");
    const mockOnMessage = jest.fn();

    const { result } = renderHook(() => useWebSocketChat());

    act(() => {
      result.current.connect("chat-token-123", mockOnMessage);
    });

    expect(createChatSocket).toHaveBeenCalledTimes(1);

    const socketParams = (createChatSocket as jest.Mock).mock.calls[0][0];
    expect(socketParams.accessToken).toBe("valid-access-token");
    expect(socketParams.chatToken).toBe("chat-token-123");

    act(() => socketParams.onOpen());
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

    act(() => socketParams.onError());
    expect(result.current.connectionState).toBe("error");
  });

  it("Happy Path: explicitly disconnecting updates state and drops the socket", () => {
    (getAccessToken as jest.Mock).mockReturnValue("valid-access-token");
    const { result } = renderHook(() => useWebSocketChat());

    act(() => {
      result.current.connect("chat-token-123", jest.fn());
    });

    act(() => {
      result.current.disconnect();
    });

    expect(mockSocketInstance.disconnect).toHaveBeenCalledTimes(1);
    expect(result.current.connectionState).toBe("disconnected");
  });
});
