"use client";

import { AnimatePresence, motion } from "motion/react";
import { X } from "lucide-react";
import type { ModalProps } from "@/types/types";

export default function Modal({
  isOpen,
  title,
  description,
  children,
  onClose,
  onConfirm,
  onCancel,
  confirmText = "Confirm",
  cancelText = "Cancel",
  isDangerous = false,
}: ModalProps) {
  async function handleConfirm() {
    const result = await onConfirm?.();
    if (result !== false) onClose();
  }

  async function handleCancel() {
    const result = await onCancel?.();
    if (result !== false) onClose();
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center px-4"
          style={{ backgroundColor: "rgba(61, 47, 77, 0.5)" }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="neu-flat w-full max-w-sm overflow-hidden p-6"
          >
            <div className="flex items-start justify-between" style={{ borderBottom: "1px solid #7a6b8f" }}>
              <div>
                <h2
                  id="modal-title"
                  className="text-lg font-semibold"
                  style={{ color: "#3d2f4d" }}
                >
                  {title}
                </h2>
                {description && (
                  <p className="mt-1 text-sm" style={{ color: "#5a4a6b" }}>
                    {description}
                  </p>
                )}
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 transition-colors neu-flat-sm"
                style={{ color: "#3d2f4d" }}
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {children && <div className="py-4">{children}</div>}

            {(onConfirm || onCancel) && (
              <div className="flex gap-3 py-4" style={{ borderTop: "1px solid #7a6b8f" }}>
                <button
                  onClick={handleCancel}
                  className="neu-btn flex-1 px-4 py-2 text-sm font-medium"
                  style={{ color: "#3d2f4d" }}
                >
                  {cancelText}
                </button>
                <button
                  onClick={handleConfirm}
                  className="neu-btn flex-1 px-4 py-2 text-sm font-medium"
                  style={{
                    color: isDangerous ? "#c44b6e" : "#3d2f4d",
                  }}
                >
                  {confirmText}
                </button>
              </div>
            )}
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
