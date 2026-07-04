import { renderHook, act } from "@testing-library/react";
import axios from "axios";
import { useChatSession } from "@/hooks/useChatSession";
import * as chatStorage from "@/services/storage/chatStorage";
import * as chatApi from "@/services/chat/chatApi";
import * as messageUtils from "@/utils/messageUtils";
import type { ChatMessage } from "@/types/types";

jest.mock("axios", () => {
  const mockAxiosInstance = {
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    delete: jest.fn(),
    patch: jest.fn(),
    interceptors: {
      request: { use: jest.fn(), eject: jest.fn() },
      response: { use: jest.fn(), eject: jest.fn() },
    },
  };

  return {
    __esModule: true,
    default: {
      create: jest.fn(() => mockAxiosInstance),
      isAxiosError: jest.fn(),
      get: jest.fn(),
      post: jest.fn(),
    },
    isAxiosError: jest.fn(),
  };
});
jest.mock("@/services/storage/chatStorage");
jest.mock("@/services/chat/chatApi");
jest.mock("@/utils/messageUtils");
jest.mock("@/services/toast/toastEvents");

describe("useChatSession Hook", () => {
  const mockInitialMessage: ChatMessage = {
    id: "msg-1",
    role: "user",
    content: "Hello",
    timestamp: 12345,
  };

  beforeEach(() => {
    jest.clearAllMocks();

    (chatStorage.getChatToken as jest.Mock).mockReturnValue("initial-token");
    (chatStorage.getChatMessages as jest.Mock).mockReturnValue([
      mockInitialMessage,
    ]);

    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("Happy Path: initializes state from localStorage", () => {
    const { result } = renderHook(() => useChatSession());

    expect(result.current.activeChatToken).toBe("initial-token");
    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe("Hello");
  });

  it("Happy Path: basic state mutations (addMessage, setMessages, clearAllMessages)", () => {
    const { result } = renderHook(() => useChatSession());
    const newMessage: ChatMessage = {
      id: "msg-2",
      role: "assistant",
      content: "Hi there",
      timestamp: 12346,
    };

    act(() => {
      result.current.addMessage(newMessage);
    });
    expect(result.current.messages).toHaveLength(2);

    act(() => {
      result.current.setMessages([newMessage]);
    });
    expect(result.current.messages).toHaveLength(1);
    expect(chatStorage.setChatMessages).toHaveBeenCalledWith([newMessage]);

    act(() => {
      result.current.clearAllMessages();
    });
    expect(result.current.messages).toHaveLength(0);
    expect(chatStorage.clearChatMessages).toHaveBeenCalledTimes(1);
  });

  it("Happy Path: auto-saves messages to local storage after 1 second debounce", () => {
    const { result } = renderHook(() => useChatSession());
    const newMessage: ChatMessage = {
      id: "msg-3",
      role: "user",
      content: "Typing...",
      timestamp: 12347,
    };

    (chatStorage.setChatMessages as jest.Mock).mockClear();

    act(() => {
      result.current.addMessage(newMessage);
    });

    expect(chatStorage.setChatMessages).not.toHaveBeenCalled();

    act(() => {
      jest.advanceTimersByTime(1000);
    });

    expect(chatStorage.setChatMessages).toHaveBeenCalledWith([
      mockInitialMessage,
      newMessage,
    ]);
  });

  describe("startNewSession", () => {
    it("Happy Path: creates a new session, wipes old state, and updates tokens", async () => {
      const { result } = renderHook(() => useChatSession());
      (chatApi.createChatSession as jest.Mock).mockResolvedValue({
        token: "new-session-token",
      });

      let newToken: string = "";
      await act(async () => {
        newToken = await result.current.startNewSession("My New Chat");
      });

      expect(chatApi.createChatSession).toHaveBeenCalledWith("My New Chat");
      expect(result.current.messages).toHaveLength(0);
      expect(result.current.input).toBe("");
      expect(result.current.activeChatToken).toBe("new-session-token");
      expect(newToken).toBe("new-session-token");

      expect(chatStorage.clearChatMessages).toHaveBeenCalledTimes(1);
      expect(chatStorage.setChatToken).toHaveBeenCalledWith(
        "new-session-token",
      );
    });
  });

  describe("loadSessionHistory", () => {
    it("Happy Path: fetches, normalizes, and returns history", async () => {
      const { result } = renderHook(() => useChatSession());
      const mockRawHistory = [{ role: "user", msg: "Hi" }];
      const mockNormalizedHistory = [
        { id: "1", role: "user", content: "Hi", timestamp: 123 },
      ];

      (chatApi.getChatHistory as jest.Mock).mockResolvedValue({
        history: mockRawHistory,
      });
      (messageUtils.normalizeHistoryMessage as jest.Mock).mockReturnValue(
        mockNormalizedHistory,
      );

      let response;
      await act(async () => {
        response = await result.current.loadSessionHistory("some-token");
      });

      expect(chatApi.getChatHistory).toHaveBeenCalledWith("some-token");
      expect(messageUtils.normalizeHistoryMessage).toHaveBeenCalledWith(
        mockRawHistory,
      );
      expect(response).toEqual({
        messages: mockNormalizedHistory,
        success: true,
      });
    });

    it("Edge Case: handles 404 Not Found gracefully by returning empty arrays", async () => {
      const { result } = renderHook(() => useChatSession());

      const mock404Error = { response: { status: 404 } };
      (axios.isAxiosError as unknown as jest.Mock).mockReturnValue(true);
      (chatApi.getChatHistory as jest.Mock).mockRejectedValue(mock404Error);

      let response;
      await act(async () => {
        response = await result.current.loadSessionHistory("expired-token");
      });

      expect(response).toEqual({ messages: [], success: false });
    });

    it("Error Condition: throws critical errors that are not 404s", async () => {
      const { result } = renderHook(() => useChatSession());

      const mock500Error = { response: { status: 500 } };
      (axios.isAxiosError as unknown as jest.Mock).mockReturnValue(true);
      (chatApi.getChatHistory as jest.Mock).mockRejectedValue(mock500Error);

      await expect(
        act(async () => {
          await result.current.loadSessionHistory("broken-token");
        }),
      ).rejects.toEqual(mock500Error);
    });
  });
});
