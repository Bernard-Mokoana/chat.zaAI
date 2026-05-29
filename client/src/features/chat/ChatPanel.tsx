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
import ChatInterface from "@/features/chat/ChatInterface";
import type { ChatMessage, ChatPanelProps, ChatSession, ConnectionState } from "@/types/types";
import { useRouter } from "next/navigation";

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
          setConnectionState("disconnected");
          setIsAssistantTyping(false);
        },
        onError: () => {
          setConnectionState("error");
          setIsAssistantTyping(false);
        },
        onMessage: (message: string) => {
          setIsAssistantTyping(false);
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
            } else if (status === 401) {
              clearAuthState();
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
          router.push("/");
          return;
        }

        clearChatToken();
        clearChatMessages();
        console.error("Failed to init chat session", error);
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
      // add setError() state
      return;
    }
    } else {
      console.warn("Cannot send message: socket not connected");
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
