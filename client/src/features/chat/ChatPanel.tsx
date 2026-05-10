"use client";

import { useEffect, useRef, useState } from "react";
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
} from "@/services/storage/chatStorage";
import ChatInterface from "@/features/chat/ChatInterface";
import type { ChatMessage, ChatPanelProps } from "@/types/types";

export default function ChatPanel({ displayName }: ChatPanelProps) {
  const [input, setInput] = useState("");
  const socketRef = useRef<ChatSocket | null>(null);
  const [connectionState, setConnectionState] = useState<
    "connecting" | "connected" | "disconnected" | "error"
  >("connecting");
  const [isAssistantTyping, setIsAssistantTyping] = useState(false);

  const [messages, setMessages] = useState<ChatMessage[]>(() => {
  const stored = getChatMessages<ChatMessage[]>();
  return stored ?? [];
});

  useEffect(() => {
    setChatMessages(messages);
  }, [messages]);

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
    let alive = true;

    async function initSession() {
      setConnectionState("connecting");
      try {
        const existingToken = getChatToken();
        const accessToken = getAccessToken();
        if (!accessToken) {
          throw new Error("Missing access token");
        }

        if (existingToken) {
          try {
            const history = await refreshChatSession(existingToken);
            if (!alive) return;

            socketRef.current = createChatSocket({
              accessToken,
              chatToken: existingToken,
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

            if (history?.messages?.length) {
              const mapped = history.messages.map((m: any) => {
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
          } catch (err: any) {
            const status = err?.response?.status;
            if (status === 401 || status === 403) {
              clearChatToken();
              clearChatMessages();
            } else {
              throw err;
            }
          }
        }

        const session = await createChatSession(displayName);
        if (!alive) return;

        setChatToken(session.token);

        socketRef.current = createChatSocket({
          accessToken,
          chatToken: session.token,
          onOpen: () => setConnectionState("connected"),
          onMessage: (message) => {
            setIsAssistantTyping(false);
            setMessages((prev) => [
              ...prev,
              { id: crypto.randomUUID(), role: "assistant", content: message },
            ]);
          },
          onClose: () => {
            setConnectionState("disconnected");
            setIsAssistantTyping(false);
          },
          onError: () => {
            setConnectionState("error");
            setIsAssistantTyping(false);
          },
        });
      } catch (error) {
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
  }, [displayName]);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmed = input.trim();
    if (!trimmed) {
      return;
    }

    if (socketRef.current && socketRef.current.isConnected()) {
      socketRef.current.send(trimmed);
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
