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
    const result = onCancel?.();
    if (result !== false) onClose();
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 px-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="modal-title"
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ duration: 0.2 }}
            className="w-full max-w-sm overflow-hidden rounded-lg bg-white shadow-xl dark:bg-slate-900"
          >
            {/* Header */}
            <div className="flex items-start justify-between border-b border-slate-200 px-6 py-4 dark:border-slate-700">
              <div>
                <h2
                  id="modal-title"
                  className="text-lg font-semibold text-slate-900 dark:text-slate-50"
                >
                  {title}
                </h2>
                {description && (
                  <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                    {description}
                  </p>
                )}
              </div>
              <button
                onClick={onClose}
                className="rounded-lg p-1.5 text-slate-400 hover:bg-slate-100 hover:text-slate-600 dark:hover:bg-slate-800 dark:hover:text-slate-300"
                aria-label="Close"
              >
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Content */}
            {children && <div className="px-6 py-4">{children}</div>}

            {/* Footer */}
            {(onConfirm || onCancel) && (
              <div className="flex gap-3 border-t border-slate-200 px-6 py-4 dark:border-slate-700">
                <button
                  onClick={handleCancel}
                  className="flex-1 rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 dark:border-slate-600 dark:text-slate-300 dark:hover:bg-slate-800"
                >
                  {cancelText}
                </button>
                <button
                  onClick={handleConfirm}
                  className={`flex-1 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors ${
                    isDangerous
                      ? "bg-rose-600 hover:bg-rose-700"
                      : "bg-blue-600 hover:bg-blue-700"
                  }`}
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