"use client";

import { useEffect, useRef, useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { MessageSquare, PanelLeftClose, PanelLeftOpen, Plus, Trash2, Clock } from "lucide-react";
import { loadSessions, deleteSession } from "@/services/storage/sessionStorage";
import type { ChatSession, ChatSidebarProps } from "@/types/types";
import { relativeTime, groupSessions } from "@/utils/helpers";

function SessionItem({session, isActive, onSelect, onDelete}: {
  session: ChatSession;
  isActive: boolean;
  onSelect: (s: ChatSession) => void;
  onDelete: (id: string) => void;
}) {
  const [hovered, setHovered] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirmDelete) {
      setConfirmDelete(true);
      timerRef.current = setTimeout(() => setConfirmDelete(false), 2500);
    } else {
      if (timerRef.current) clearTimeout(timerRef.current);
      onDelete(session.id);
    }
  };

  useEffect(() => {
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current);
    };
  }, []);

  return (
    <motion.div
      layout
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -8, height: 0, marginBottom: 0 }}
      transition={{ duration: 0.18 }}
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => {
        setHovered(false);
        setConfirmDelete(false);
      }}
      onClick={() => onSelect(session)}
      className={`group relative flex cursor-pointer flex-col gap-1 rounded-xl px-3 py-2.5 transition-all duration-150 ${
        isActive
          ? "card-active"
          : "card-sm"
      }`}
      style={{ color: isActive ? "var(--text)" : "var(--text-secondary)" }}
    >
      <div className="flex items-start justify-between gap-2">
        <span
          className="line-clamp-1 text-sm font-semibold leading-snug"
        >
          {session.title}
        </span>

        <AnimatePresence>
          {hovered && (
            <motion.button
              initial={{ opacity: 0, scale: 0.7 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.7 }}
              transition={{ duration: 0.12 }}
              onClick={handleDelete}
              className="shrink-0 rounded-md p-1 transition-colors card-sm"
              style={{
                color: confirmDelete ? "var(--danger)" : isActive ? "var(--text)" : "var(--text-secondary)",
                backgroundColor: "var(--border)"
              }}
              title={confirmDelete ? "Click again to confirm" : "Delete"}
            >
              <Trash2 className="h-3 w-3" />
            </motion.button>
          )}
        </AnimatePresence>
      </div>
      <p
        className="line-clamp-1 text-xs"
        style={{ color: isActive ? "var(--text)" : "var(--text-muted)" }}
      >
        {session.preview || "No messages yet"}
      </p>
      <div
        className="flex items-center gap-1 text-[10px]"
        style={{ color: isActive ? "var(--text)" : "var(--text-muted)" }}
      >
        <Clock className="h-2.5 w-2.5" />
        {relativeTime(session.updatedAt)}
      </div>
    </motion.div>
  );
}

function SectionLabel({ label }: { label: string }) {
  return (
    <p className="mb-1 mt-3 px-3 text-[10px] font-bold uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
      {label}
    </p>
  );
}

export default function ChatSidebar({
  activeSessionId,
  onSelectSession,
  onNewChat,
  onDeleteSession,
  liveMessages = [],
  refreshTrigger = 0,
}: ChatSidebarProps & { refreshTrigger?: number}) {
  const [isOpen, setIsOpen] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([]);

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setSessions(loadSessions());
    }, 0);

    return () => window.clearTimeout(timeoutId);
  }, [activeSessionId, refreshTrigger, liveMessages.length]);

  const handleDelete = (id: string) => {
    deleteSession(id);
    setSessions(loadSessions());
    onDeleteSession?.(id);
  };

  const { today, yesterday, older } = groupSessions(sessions);

  if (!isOpen) {
    return (
      <motion.aside
        key="collapsed"
        initial={{ width: 56 }}
        animate={{ width: 56 }}
        className="relative flex h-screen flex-col items-center border-r py-4 gap-3"
        style={{ minWidth: 56, backgroundColor: "var(--surface-2)", borderColor: "var(--border)" }}
      >
        <button
          onClick={() => setIsOpen(true)}
          className="rounded-lg p-2 transition-colors card-sm"
          style={{ color: "var(--text)" }}
          title="Open sidebar"
        >
          <PanelLeftOpen className="h-5 w-5" />
        </button>
        <button
          onClick={onNewChat}
          className="rounded-lg p-2 transition-colors card-sm"
          style={{ color: "var(--text)" }}
          title="New chat"
        >
          <Plus className="h-5 w-5" />
        </button>
        <div className="mt-2 flex flex-col gap-2 w-full items-center">
          {sessions.slice(0, 6).map((s) => (
            <button
              key={s.id}
              onClick={() => onSelectSession(s)}
              title={s.title}
              className="rounded-lg p-2 transition-colors card-sm"
              style={{ color: s.id === activeSessionId ? "var(--text)" : "var(--text-secondary)", backgroundColor: s.id === activeSessionId ? "var(--surface-3)" : "var(--surface-3)" }}
            >
              <MessageSquare className="h-4 w-4" />
            </button>
          ))}
        </div>
      </motion.aside>
    );
  }
  return (
    <motion.aside
      key="expanded"
      initial={{ width: 0, opacity: 0 }}
      animate={{ width: 272, opacity: 1 }}
      exit={{ width: 0, opacity: 0 }}
      transition={{ duration: 0.22, ease: "easeInOut" }}
      className="flex h-screen flex-col overflow-hidden"
      style={{ minWidth: 272, maxWidth: 272, backgroundColor: "var(--surface-2)", borderRight: "1px solid var(--border)" }}
    >
      <div className="flex items-center justify-between px-4 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4" style={{ color: "var(--accent)" }} />
          <span className="text-sm font-bold tracking-tight" style={{ color: "var(--text)" }}>
            Chat History
          </span>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="rounded-lg p-1.5 transition-colors card-sm"
          style={{ color: "var(--text)" }}
          title="Collapse sidebar"
        >
          <PanelLeftClose className="h-4 w-4" />
        </button>
      </div>

      <div className="px-3 pt-3">
        <button
          onClick={onNewChat}
          className="btn flex w-full items-center justify-center gap-2 py-2.5 text-sm font-semibold"
          style={{ color: "var(--accent-text)" }}
        >
          <Plus className="h-4 w-4" />
          New conversation
        </button>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4 scrollbar-thin scrollbar-thumb-slate-200">
        {sessions.length === 0 ? (
          <div className="mt-10 flex flex-col items-center gap-2 text-center">
            <MessageSquare className="h-8 w-8" style={{ color: "var(--border-strong)" }} />
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>No conversations yet.</p>
            <p className="text-xs" style={{ color: "var(--text-muted)" }}>Start chatting to see history here.</p>
          </div>
        ) : (
          <>
            {today.length > 0 && (
              <>
                <SectionLabel label="Today" />
                <AnimatePresence>
                  {today.map((s) => (
                    <SessionItem
                      key={s.id}
                      session={s}
                      isActive={s.id === activeSessionId}
                      onSelect={onSelectSession}
                      onDelete={handleDelete}
                    />
                  ))}
                </AnimatePresence>
              </>
            )}
            {yesterday.length > 0 && (
              <>
                <SectionLabel label="Yesterday" />
                <AnimatePresence>
                  {yesterday.map((s) => (
                    <SessionItem
                      key={s.id}
                      session={s}
                      isActive={s.id === activeSessionId}
                      onSelect={onSelectSession}
                      onDelete={handleDelete}
                    />
                  ))}
                </AnimatePresence>
              </>
            )}
            {older.length > 0 && (
              <>
                <SectionLabel label="Earlier" />
                <AnimatePresence>
                  {older.map((s) => (
                    <SessionItem
                      key={s.id}
                      session={s}
                      isActive={s.id === activeSessionId}
                      onSelect={onSelectSession}
                      onDelete={handleDelete}
                    />
                  ))}
                </AnimatePresence>
              </>
            )}
          </>
        )}
      </div>
      <div className="px-4 py-3" style={{ borderTop: "1px solid var(--border)" }}>
        <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
          {sessions.length} conversation{sessions.length !== 1 ? "s" : ""} saved locally
        </p>
      </div>
    </motion.aside>
  );
}
