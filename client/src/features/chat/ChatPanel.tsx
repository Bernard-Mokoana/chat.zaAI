"use client";

import { useEffect, useRef, useState } from "react";
import axios from "axios";
import { createChatSession, refreshChatSession } from "@/services/chat/chatApi";
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

  const parseHistoryMessage = (raw: string) => {
    const trimmed = raw.trim();
    if (trimmed.toLowerCase().startsWith("human:")) {
      return { role: "user" as const, content: trimmed.replace(/^human:\s*/i, "") };
    }
    if (trimmed.toLowerCase().startsWith("bot:")) {
      return { role: "assistant" as const, content: trimmed.replace(/^bot:\s*/i, "") };
    }
    return { role: "assistant" as const, content: trimmed };
  };

  useEffect(() => {
    const handleLoadSession = (event: Event) => {
      const session = (event as CustomEvent<ChatSession>).detail;
      const sessionMessages = session?.messages ?? [];

      setInput("");
      setIsAssistantTyping(false);
      setMessages(sessionMessages);
      setChatMessages(sessionMessages);
    };

    const handleNewSession = () => {
      setInput("");
      setIsAssistantTyping(false);
      setMessages([]);
      clearChatMessages();
    };

    window.addEventListener("chat:load-session", handleLoadSession);
    window.addEventListener("chat:new-session", handleNewSession);

    return () => {
      window.removeEventListener("chat:load-session", handleLoadSession);
      window.removeEventListener("chat:new-session", handleNewSession);
    };
  }, []);

  useEffect(() => {
    let alive = true;

    function openSocket(chatToken: string) {
      const accessToken = getAccessToken();

      if (!accessToken) {
        throw new Error("Access token is required to connect to chat");
      }

      socketRef.current = createChatSocket({
        accessToken,
        chatToken,
        onOpen: () => setConnectionState("connected"),
        onClose: () => {
          if (!alive) return;
          setConnectionState("disconnected");
          setIsAssistantTyping(false);
          showToast({
            title: "Chat disconnected",
            description: "Messages pause until the connection is restored.",
            tone: "warning",
          });
        },
        onError: () => {
          if (!alive) return;
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
    }

    async function initSession() {
      setConnectionState("connecting");
      try {
        const existingToken = getChatToken();

        if (existingToken) {
          try {
            const history = await refreshChatSession(existingToken);
            if (!alive) return;

            openSocket(existingToken);

            if (history?.messages?.length) {
              const mapped = history.messages.map((m) => {
                const parsed = parseHistoryMessage(m.msg ?? "");
                return {
                  id: m.id ?? crypto.randomUUID(),
                  role: parsed.role,
                  content: parsed.content,
                };
              });

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
      socketRef.current?.disconnect();
    };
  }, [displayName, router]);

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
      connectionState={connectionState}
      messages={messages}
      input={input}
      onInputChange={setInput}
      onSubmit={handleSubmit}
      isAssistantTyping={isAssistantTyping}
    />
  );
}
