"use client";

import { useCallback, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import type { ChatInterfaceProps, ChatMessage, ChatSession } from "@/types/types";
import { clearAuthState } from "@/services/storage/chatStorage";
import { logout } from "@/services/auth/authApi";
import { showToast } from "@/services/toast/toastEvents";
import { useSessionManagement } from "@/hooks/useSessionManagement";
import ChatSidebar from "./ChatSidebar";
import ChatHeader from "./ChatHeader";
import ChatMessageList from "./ChatMessageList";
import ChatInput from "./ChatInput";

export default function ChatInterface({
  displayName,
  chatToken,
  connectionState,
  messages,
  input,
  onInputChange,
  onSubmit,
  isAssistantTyping,
}: ChatInterfaceProps) {
  const router = useRouter();
  const {
    activeSessionId,
    setActiveSessionId,
    saveCurrentSession,
    deleteCurrentSession,
  } = useSessionManagement();
  useEffect(() => {
    if (!chatToken) return;
    if (activeSessionId) return;
    setActiveSessionId(chatToken);
  }, [chatToken, activeSessionId, setActiveSessionId]);

  useEffect(() => {
    const handleSessionReady = (event: Event) => {
      const { token } = (event as CustomEvent<{ token: string }>).detail;
      if (token && token !== activeSessionId) {
        setActiveSessionId(token);
        const placeholder: ChatSession = {
          id: token,
          chatToken: token,
          title: "New conversation",
          preview: "",
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        };
        saveCurrentSession(placeholder);
      }
    };

    window.addEventListener("chat:session-ready", handleSessionReady);
    return () => window.removeEventListener("chat:session-ready", handleSessionReady);
  }, [activeSessionId, setActiveSessionId, saveCurrentSession]);

  const createdAtRef = useRef<Record<string, number>>({});

  useEffect(() => {
    if (!activeSessionId || messages.length === 0) return;

    if (!createdAtRef.current[activeSessionId]) {
      createdAtRef.current[activeSessionId] = Date.now();
    }

    const lastMsg = messages[messages.length - 1];
    const session: ChatSession = {
      id: activeSessionId,
      chatToken: chatToken ?? undefined,
      title: messages[0]?.content?.slice(0, 40) ?? "New conversation",
      preview: lastMsg?.content?.slice(0, 80) ?? "",
      messages: messages as ChatMessage[],
      createdAt: createdAtRef.current[activeSessionId],
      updatedAt: Date.now(),
    };

    saveCurrentSession(session);
  }, [messages, activeSessionId, chatToken, saveCurrentSession]);

  const handleSelectSession = useCallback(
    (session: ChatSession) => {
      setActiveSessionId(session.id);
      window.dispatchEvent(
        new CustomEvent("chat:load-session", { detail: session })
      );
    },
    [setActiveSessionId]
  );

  const handleNewChat = useCallback(() => {
    setActiveSessionId(null);
    window.dispatchEvent(new CustomEvent("chat:new-session"));
  }, [setActiveSessionId]);

  const handleDeleteSession = useCallback(
    (id: string) => {
      deleteCurrentSession(id);
      if (id === activeSessionId) {
        handleNewChat();
      }
    },
    [activeSessionId, deleteCurrentSession, handleNewChat]
  );

  const handleLogout = useCallback(async () => {
    try {
      await logout();
      showToast({
        title: "Signed out",
        description: "Your session has been closed.",
        tone: "success",
      });
    } catch {
      showToast({
        title: "Signed out locally",
        description: "We could not reach the server, but your local session was cleared.",
        tone: "warning",
      });
    } finally {
      clearAuthState();
      router.push("/");
    }
  }, [router]);

  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      onSubmit(event);
    },
    [onSubmit]
  );

  return (
    <div className="flex h-screen w-full overflow-hidden" style={{ backgroundColor: "var(--bg)" }}>
      <ChatSidebar
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        liveMessages={messages as ChatMessage[]}
      />

      <div className="flex flex-1 flex-col overflow-hidden">
        <ChatHeader
          displayName={displayName}
          connectionState={connectionState}
          onLogout={handleLogout}
        />

        <ChatMessageList
          messages={messages}
          connectionState={connectionState}
          isAssistantTyping={isAssistantTyping}
        />
        <ChatInput
          value={input}
          onChange={onInputChange}
          onSubmit={handleSubmit}
          disabled={connectionState === "error"}
        />
      </div>
    </div>
  );
}
