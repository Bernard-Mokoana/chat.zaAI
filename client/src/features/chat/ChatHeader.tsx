"use client";

import { LogOut } from "lucide-react";
import { useCallback, useState } from "react";
import Modal from "@/components/Modal";
import type { ChatHeaderProps } from "@/types/types";

const connectionTone = {
  connected: {
    label: "Connected",
    badge: "var(--status-success)",
    text: "var(--status-text)",
    dot: "var(--status-success-dot)",
  },
  connecting: {
    label: "Connecting",
    badge: "var(--status-warning)",
    text: "var(--status-text)",
    dot: "var(--status-warning-dot)",
  },
  disconnected: {
    label: "Offline",
    badge: "var(--surface-3)",
    text: "var(--text)",
    dot: "var(--border-strong)",
  },
  error: {
    label: "Error",
    badge: "var(--status-error)",
    text: "var(--status-text)",
    dot: "var(--status-error-dot)",
  },
} as const;

export default function ChatHeader({
  displayName,
  connectionState,
  onLogout,
}: ChatHeaderProps) {
  const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);
  const status = connectionTone[connectionState];

  const handleLogoutClick = useCallback(() => {
    setIsLogoutModalOpen(true);
  }, []);

  const handleConfirmLogout = useCallback(() => {
    setIsLogoutModalOpen(false);
    onLogout();
  }, [onLogout]);

  return (
    <>
      <header className="card-sm w-full" style={{ borderRadius: "0 0 40px 40px", borderBottomLeftRadius: "40px", borderBottomRightRadius: "40px" }}>
        <div className="mx-auto flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              type="button"
              onClick={handleLogoutClick}
              className="btn rounded-lg p-2"
              aria-label="Logout"
              title="Logout"
            >
              <LogOut className="h-5 w-5" style={{ color: "var(--accent-text)" }} />
            </button>

            <div>
              <h2 className="text-lg font-semibold" style={{ color: "var(--text)" }}>
                chat.zaAI
              </h2>
              <p className="text-sm" style={{ color: "var(--text-secondary)" }}>
                Welcome {displayName}
              </p>
            </div>
          </div>

          <div
            className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold"
            style={{ backgroundColor: status.badge, color: status.text }}
          >
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: status.dot }} />
            {status.label}
          </div>
        </div>
      </header>

      <Modal
        isOpen={isLogoutModalOpen}
        title="Logout"
        description="Are you sure you want to logout?"
        onClose={() => setIsLogoutModalOpen(false)}
        onConfirm={handleConfirmLogout}
        confirmText="Logout"
        isDangerous
      />
    </>
  );
}
