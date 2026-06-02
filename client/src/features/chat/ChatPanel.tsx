"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import axios from "axios";
import { createChatSession, getChatHistory, refreshChatSession } from "@/services/chat/chatApi";
import { ChatSocket, createChatSocket } from "@/services/ws/chatSocket";
import {
  getChatToken,
  getAccessToken,
  setChatToken,
  clearChatToken,
  getChatMessages,
  setChatMessages,
  clearChatMessages,
  clearAuthState,
} from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import ChatInterface from "@/features/chat/ChatInterface";
import type { ChatMessage, ChatPanelProps, ChatSession, ConnectionState } from "@/types/types";
import { useRouter } from "next/navigation";

const WS_RATE_LIMIT_MESSAGE = "Too many messages.";

export default function ChatPanel({ displayName }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const socketRef = useRef<ChatSocket | null>(null);
  const [connectionState, setConnectionState] = useState<ConnectionState>("connecting");
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);
  const [activeChatToken, setActiveChatToken] = useState<string | null>(() => getChatToken());
  const suppressNextCloseRef = useRef(false);
  const [messages, setMessages] = useState<ChatMessage[]>(() => {
    const stored = getChatMessages<ChatMessage[]>();
    return stored ?? [];
});
 const [debouncedMessages, setDebouncedMessages] = useState(messages);
 const router = useRouter()

  useEffect(() => {
    const timeoutId = setTimeout(() => {
      setDebouncedMessages(messages);
    }, 1000);
    return () => clearTimeout(timeoutId);
  }, [messages]);

  useEffect(() => {
    setChatMessages(debouncedMessages);
  }, [debouncedMessages]);

  const parseHistoryMessage = (raw: string, role?: string) => {
    const trimmed = raw.trim();
    const normalizedRole = role?.toLowerCase();

    if (normalizedRole === "human" || normalizedRole === "user") {
      return { role: "user" as const, content: trimmed.replace(/^human:\s*/i, "") };
    }

    if (normalizedRole === "bot" || normalizedRole === "assistant") {
      return { role: "assistant" as const, content: trimmed.replace(/^bot:\s*/i, "") };
    }

    if (trimmed.toLowerCase().startsWith("human:")) {
      return { role: "user" as const, content: trimmed.replace(/^human:\s*/i, "") };
    }
    if (trimmed.toLowerCase().startsWith("bot:")) {
      return { role: "assistant" as const, content: trimmed.replace(/^bot:\s*/i, "") };
    }
    return { role: "assistant" as const, content: trimmed };
  };

  const mapHistoryMessages = useCallback((history: { id?: string; msg?: string; role?: string }[]) => {
    return history.map((m) => {
      const parsed = parseHistoryMessage(m.msg ?? "", m.role);
      return {
        id: m.id ?? crypto.randomUUID(),
        role: parsed.role,
        content: parsed.content,
      };
    });
  }, []);

  const openSocket = useCallback((chatToken: string) => {
    const accessToken = getAccessToken();

    if (!accessToken) {
      throw new Error("Access token is required to connect to chat");
    }

    if (socketRef.current) {
      suppressNextCloseRef.current = true;
      socketRef.current.disconnect();
    }

    socketRef.current = createChatSocket({
      accessToken,
      chatToken,
      onOpen: () => setConnectionState("connected"),
      onClose: () => {
        if (suppressNextCloseRef.current) {
          suppressNextCloseRef.current = false;
          return;
        }

        setConnectionState("disconnected");
        setIsAssistantTyping(false);
        showToast({
          title: "Chat disconnected",
          description: "Messages pause until the connection is restored.",
          tone: "warning",
        });
      },
      onError: () => {
        setConnectionState("error");
        setIsAssistantTyping(false);
        showToast({
          title: "Chat connection problem",
          description: "The live chat connection could not stay open.",
          tone: "error",
        });
      },
      onMessage: (message: string) => {
        setIsAssistantTyping(false);

        if (message.startsWith(WS_RATE_LIMIT_MESSAGE)) {
          showToast({
            title: "Message limit reached",
            description: "Please wait a moment before sending another message.",
            tone: "warning",
          });
          return;
        }

        setMessages((prev) => [
          ...prev,
          { id: crypto.randomUUID(), role: "assistant", content: message },
        ]);
      },
    });
  }, []);

  const startNewBackendSession = useCallback(async () => {
    setConnectionState("connecting");
    setInput("");
    setIsAssistantTyping(false);
    setMessages([]);
    clearChatMessages();
    clearChatToken();
    setActiveChatToken(null);

    const session = await createChatSession(displayName);
    setChatToken(session.token);
    setActiveChatToken(session.token);
    openSocket(session.token);
    return session.token;
  }, [displayName, openSocket]);

  useEffect(() => {
    const handleLoadSession = async (event: Event) => {
      const session = (event as CustomEvent<ChatSession>).detail;
      const sessionMessages = session?.messages ?? [];
      const chatToken = session?.chatToken ?? session?.id;

      setInput("");
      setIsAssistantTyping(false);
      setMessages(sessionMessages);
      setChatMessages(sessionMessages);

      if (!chatToken || chatToken.startsWith("session_")) {
        return;
      }

      try {
        setConnectionState("connecting");
        setChatToken(chatToken);
        setActiveChatToken(chatToken);
        openSocket(chatToken);

        let mapped = sessionMessages;
        try {
          const response = await getChatHistory(chatToken);
          mapped = mapHistoryMessages(response.history ?? []);
        } catch (error) {
          const status = axios.isAxiosError(error) ? error.response?.status : undefined;
          if (status !== 404) {
            throw error;
          }
        }

        if (mapped.length) {
          setMessages(mapped);
          setChatMessages(mapped);
        }
      } catch (error) {
        const status = axios.isAxiosError(error) ? error.response?.status : undefined;
        if (status === 401) {
          clearAuthState();
          router.push("/");
          return;
        }

        showToast({
          title: "Could not load history",
          description: "The saved conversation could not be restored from the server.",
          tone: "error",
        });
      }
    };

    const handleNewSession = () => {
      startNewBackendSession().catch((error) => {
        const status = axios.isAxiosError(error) ? error.response?.status : undefined;
        if (status === 401) {
          clearAuthState();
          router.push("/");
          return;
        }

        setConnectionState("error");
        showToast({
          title: "Could not start chat",
          description: "A new chat session could not be prepared.",
          tone: "error",
        });
      });
    };

    window.addEventListener("chat:load-session", handleLoadSession);
    window.addEventListener("chat:new-session", handleNewSession);

    return () => {
      window.removeEventListener("chat:load-session", handleLoadSession);
      window.removeEventListener("chat:new-session", handleNewSession);
    };
  }, [mapHistoryMessages, openSocket, router, startNewBackendSession]);

  useEffect(() => {
    let alive = true;

    async function initSession() {
      setConnectionState("connecting");
      try {
        const existingToken = getChatToken();

        if (existingToken) {
          try {
            const history = await refreshChatSession(existingToken);
            if (!alive) return;

            openSocket(existingToken);
            setActiveChatToken(existingToken);

            let mapped = mapHistoryMessages(history.messages ?? []);
            try {
              const persistedHistory = await getChatHistory(existingToken);
              if (!alive) return;
              if (persistedHistory.history?.length) {
                mapped = mapHistoryMessages(persistedHistory.history);
              }
            } catch (error) {
              const status = axios.isAxiosError(error) ? error.response?.status : undefined;
              if (status !== 404) {
                throw error;
              }
            }

            if (mapped.length) {
              setMessages((prev) => (prev.length ? prev : mapped));
            }

            return;
          } catch (error: unknown) {
            const status = axios.isAxiosError(error) ? error.response?.status : undefined;
            if (status === 403) {
              clearChatToken();
              clearChatMessages();
              showToast({
                title: "Chat session expired",
                description: "A fresh chat session is being created.",
                tone: "info",
              });
            } else if (status === 401) {
              clearAuthState();
              showToast({
                title: "Sign in again",
                description: "Your session expired. Please sign in to continue.",
                tone: "warning",
              });
              router.push("/");
              return;
            } else {
              throw error;
            }
          }
        }

        const session = await createChatSession(displayName);
        if (!alive) return;

        setChatToken(session.token);
        setActiveChatToken(session.token);
        openSocket(session.token);
      } catch (error) {
        const status = axios.isAxiosError(error) ? error.response?.status : undefined;
        if (status === 401) {
          clearAuthState();
          showToast({
            title: "Sign in again",
            description: "Your session expired. Please sign in to continue.",
            tone: "warning",
          });
          router.push("/");
          return;
        }

        clearChatToken();
        clearChatMessages();
        console.error("Failed to init chat session", error);
        showToast({
          title: "Could not start chat",
          description: "The chat session could not be prepared. Please try again.",
          tone: "error",
        });
        setConnectionState("error");
      }
    }

    initSession();

    return () => {
      alive = false;
      suppressNextCloseRef.current = true;
      socketRef.current?.disconnect();
    };
  }, [displayName, mapHistoryMessages, openSocket, router]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }

    if (socketRef.current && socketRef.current.isConnected()) {
    try {
      socketRef.current.send(trimmed);
    } catch(error) {
      console.error("Failed to send message", error);
      showToast({
        title: "Message not sent",
        description: "The chat connection rejected the message. Try again in a moment.",
        tone: "error",
      });
      return;
    }
    } else {
      console.warn("Cannot send message: socket not connected");
      showToast({
        title: "Chat is not connected",
        description: "Wait for the connection to come back before sending another message.",
        tone: "warning",
      });
      return;
    }

    setMessages((prev) => [
      ...prev,
      { id: crypto.randomUUID(), role: "user", content: trimmed },
    ]);

    setIsAssistantTyping(true);

    setInput("");
  };

  return (
    <ChatInterface
      displayName={displayName}
      chatToken={activeChatToken}
      connectionState={connectionState}
      messages={messages}
      input={input}
      onInputChange={setInput}
      onSubmit={handleSubmit}
      isAssistantTyping={isAssistantTyping}
    />
  );
}
