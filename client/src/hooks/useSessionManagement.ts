import { useState, useCallback } from "react";
import type { ChatSession, ChatMessage } from "@/types/types";
import {
  loadSessions,
  saveSession,
  deleteSession,
  getActiveSessionId,
  setActiveSessionId as setActiveSessionIdStorage,
  createSession,
} from "@/services/storage/sessionStorage";

interface UseSessionManagementReturn {
  sessions: ChatSession[];
  activeSessionId: string | null;
  setActiveSessionId: (id: string | null) => void;
  saveCurrentSession: (session: ChatSession) => void;
  deleteCurrentSession: (id: string) => void;
  createNewSession: (
    firstMessage?: ChatMessage,
    chatToken?: string,
  ) => ChatSession;
  refreshSessions: () => void;
}

/**
 * Custom hook to manage chat sessions
 * Handles session persistence and state management
 */
export function useSessionManagement(): UseSessionManagementReturn {
  const [sessions, setSessions] = useState<ChatSession[]>(() => loadSessions());
  const [activeSessionId, setActiveSessionIdState] = useState<string | null>(
    () => getActiveSessionId(),
  );

  const setActiveSessionId = useCallback((id: string | null) => {
    setActiveSessionIdState(id);
    setActiveSessionIdStorage(id);
  }, []);

  const saveCurrentSession = useCallback((session: ChatSession) => {
    saveSession(session);
    setSessions((prev) => {
      const existing = prev.findIndex((s) => s.id === session.id);
      if (existing >= 0) {
        const updated = [...prev];
        updated[existing] = session;
        return updated;
      }
      return [session, ...prev];
    });
  }, []);

  const deleteCurrentSession = useCallback(
    (id: string) => {
      deleteSession(id);
      setSessions((prev) => prev.filter((s) => s.id !== id));

      // Clear active session if deleted
      if (id === activeSessionId) {
        setActiveSessionId(null);
      }
    },
    [activeSessionId, setActiveSessionId],
  );

  const createNewSession = useCallback(
    (firstMessage?: ChatMessage, chatToken?: string): ChatSession => {
      return createSession(firstMessage, chatToken);
    },
    [],
  );

  const refreshSessions = useCallback(() => {
    setSessions(loadSessions());
  }, []);

  return {
    sessions,
    activeSessionId,
    setActiveSessionId,
    saveCurrentSession,
    deleteCurrentSession,
    createNewSession,
    refreshSessions,
  };
}
