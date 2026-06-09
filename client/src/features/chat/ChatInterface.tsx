"use client";

import { useCallback, useEffect, useState } from "react";
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
    sessions,
    activeSessionId,
    setActiveSessionId,
    saveCurrentSession,
    deleteCurrentSession,
  } = useSessionManagement();

  // Persist messages to active session
  useEffect(() => {
    if (!activeSessionId || messages.length === 0) return;

    const lastMsg = messages[messages.length - 1];
    const session: ChatSession = {
      id: activeSessionId,
      chatToken,
      title: messages[0]?.content?.slice(0, 40) ?? "New conversation",
      preview: lastMsg?.content?.slice(0, 80) ?? "",
      messages: messages as ChatMessage[],
      createdAt: Date.now(),
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
    <div className="flex h-screen w-full overflow-hidden bg-slate-50 dark:bg-slate-900">
      {/* Sidebar */}
      <ChatSidebar
        activeSessionId={activeSessionId}
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
        onDeleteSession={handleDeleteSession}
        liveMessages={messages as ChatMessage[]}
      />

      {/* Main Chat Area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <ChatHeader
          displayName={displayName}
          connectionState={connectionState}
          onLogout={handleLogout}
        />

        {/* Messages */}
        <ChatMessageList
          messages={messages}
          connectionState={connectionState}
          isAssistantTyping={isAssistantTyping}
        />

        {/* Input */}
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
