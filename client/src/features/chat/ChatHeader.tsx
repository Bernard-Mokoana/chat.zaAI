"use client";

import { ArrowLeft } from "lucide-react";
import { useCallback, useState } from "react";
import type { ConnectionState } from "@/types/types";
import Modal from "@/components/Modal";
import type { ChatHeaderProps } from "@/types/types";

const connectionTone = {
  connected: {
    label: "Connected",
    badge: "bg-emerald-500/15 text-emerald-700 dark:bg-emerald-500/20 dark:text-emerald-400",
    dot: "bg-emerald-500",
  },
  connecting: {
    label: "Connecting",
    badge: "bg-amber-500/15 text-amber-700 dark:bg-amber-500/20 dark:text-amber-400",
    dot: "bg-amber-500",
  },
  disconnected: {
    label: "Offline",
    badge: "bg-slate-500/15 text-slate-700 dark:bg-slate-500/20 dark:text-slate-400",
    dot: "bg-slate-500",
  },
  error: {
    label: "Error",
    badge: "bg-rose-500/15 text-rose-700 dark:bg-rose-500/20 dark:text-rose-400",
    dot: "bg-rose-500",
  },
} as const;

/**
 * Chat interface header with status and logout button
 */
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
      <header className="w-full border-b border-slate-200 bg-white">
        <div className="mx-auto flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              type="button"
              onClick={handleLogoutClick}
              className="rounded-lg p-2 transition-colors hover:bg-slate-100"
              aria-label="Logout"
              title="Logout"
            >
              <ArrowLeft className="h-5 w-5 text-slate-600" />
            </button>

            <div>
              <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
                AI Assistant
              </h2>
              <p className="text-sm text-slate-500 dark:text-slate-400">
                Welcome {displayName}
              </p>
            </div>
          </div>

          <div
            className={`inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold ${status.badge}`}
          >
            <span className={`h-2 w-2 rounded-full ${status.dot}`} />
            {status.label}
          </div>
        </div>
      </header>

      {/* Logout Confirmation Modal */}
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
