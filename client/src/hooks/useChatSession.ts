import { useCallback, useState, useRef, useEffect } from "react";
import type { ChatMessage, ChatSession } from "@/types/types";
import {
  getChatToken,
  setChatToken,
  clearChatToken,
  getChatMessages,
  setChatMessages,
  clearChatMessages,
} from "@/services/storage/chatStorage";
import {
  createChatSession,
  getChatHistory,
  refreshChatSession,
} from "@/services/chat/chatApi";
import { showToast } from "@/services/toast/toastEvents";
import axios from "axios";
import type { UseChatSessionReturn } from "@/types/types";

export function useChatSession(): UseChatSessionReturn {
  const [activeChatToken, setActiveChatToken] = useState<string | null>(() =>
    getChatToken(),
  );
  const [messages, setMessagesState] = useState<ChatMessage[]>(() => {
    const stored = getChatMessages<ChatMessage[]>();
    return stored ?? [];
  });
  const [input, setInput] = useState("");
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const debouncedMessagesRef = useRef<ChatMessage[]>(messages);

  // Debounce message persistence to local storage
  useEffect(() => {
    const timeoutId = setTimeout(() => {
      debouncedMessagesRef.current = messages;
      setChatMessages(messages);
    }, 1000);
    return () => clearTimeout(timeoutId);
  }, [messages]);

  const startNewSession = useCallback(
    async (displayName: string): Promise<string> => {
      setInput("");
      setIsAssistantTyping(false);
      setMessagesState([]);
      clearChatMessages();
      clearChatToken();
      setActiveChatToken(null);

      const session = await createChatSession(displayName);
      setChatToken(session.token);
      setActiveChatToken(session.token);
      return session.token;
    },
    [],
  );

  const loadSessionHistory = useCallback(
    async (
      token: string,
    ): Promise<{ messages: ChatMessage[]; success: boolean }> => {
      try {
        const response = await getChatHistory(token);
        const mappedMessages = (response.history ?? [])
          .map((m) => {
            const normalizedRole = m.role?.toLowerCase();
            const isUser =
              normalizedRole === "human" || normalizedRole === "user";
            const role = isUser ? ("user" as const) : ("assistant" as const);

            return {
              id: m.id ?? crypto.randomUUID(),
              role,
              content: (m.msg ?? "").trim().replace(/^(human|bot):\s*/i, ""),
            };
          })
          .filter((m) => m.content.length > 0);

        return { messages: mappedMessages, success: true };
      } catch (error) {
        const status = axios.isAxiosError(error)
          ? error.response?.status
          : undefined;
        if (status !== 404) {
          throw error;
        }
        return { messages: [], success: false };
      }
    },
    [],
  );

  const addMessage = useCallback((message: ChatMessage) => {
    setMessagesState((prev) => [...prev, message]);
  }, []);

  const clearAllMessages = useCallback(() => {
    setMessagesState([]);
    clearChatMessages();
  }, []);

  const setMessages = useCallback((newMessages: ChatMessage[]) => {
    setMessagesState(newMessages);
    setChatMessages(newMessages);
  }, []);

  return {
    activeChatToken,
    messages,
    input,
    isAssistantTyping,
    setInput,
    setMessages,
    setIsAssistantTyping,
    startNewSession,
    loadSessionHistory,
    addMessage,
    clearAllMessages,
  };
}
