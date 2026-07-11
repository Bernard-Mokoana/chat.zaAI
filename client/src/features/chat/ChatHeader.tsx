"use client";

import { LogOut } from "lucide-react";
import { useCallback, useState } from "react";
import Modal from "@/components/Modal";
import type { ChatHeaderProps } from "@/types/types";

const connectionTone = {
  connected: {
    label: "Connected",
    badge: "#6bcf7f",
    text: "#3d2f4d",
    dot: "#2ea04f",
  },
  connecting: {
    label: "Connecting",
    badge: "#f0c060",
    text: "#3d2f4d",
    dot: "#c49a30",
  },
  disconnected: {
    label: "Offline",
    badge: "#7a6b8f",
    text: "#f5f0fa",
    dot: "#615676",
  },
  error: {
    label: "Error",
    badge: "#e88ba0",
    text: "#3d2f4d",
    dot: "#c44b6e",
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
      <header className="neu-flat-sm w-full" style={{ borderRadius: "0 0 40px 40px", borderBottomLeftRadius: "40px", borderBottomRightRadius: "40px" }}>
        <div className="mx-auto flex flex-wrap items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <div className="flex items-center gap-3 sm:gap-4">
            <button
              type="button"
              onClick={handleLogoutClick}
              className="neu-btn rounded-lg p-2"
              aria-label="Logout"
              title="Logout"
            >
              <LogOut className="h-5 w-5" style={{ color: "#3d2f4d" }} />
            </button>

            <div>
              <h2 className="text-lg font-semibold" style={{ color: "#3d2f4d" }}>
                3DoT
              </h2>
              <p className="text-sm" style={{ color: "#5a4a6b" }}>
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
