"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import { AnimatePresence, motion } from "motion/react";
import { onToast } from "@/services/toast/toastEvents";
import type { ToastItem } from "@/types/types";

const TOAST_DURATION_MS = 4500;
const MAX_VISIBLE_TOASTS = 3;

const toneStyles = {
  info: {
    icon: Info,
    className: "border-sky-200 bg-sky-50 text-sky-950",
    accentClassName: "bg-sky-500",
    iconClassName: "text-sky-600",
  },
  success: {
    icon: CheckCircle2,
    className: "border-emerald-200 bg-emerald-50 text-emerald-950",
    accentClassName: "bg-emerald-500",
    iconClassName: "text-emerald-600",
  },
  warning: {
    icon: AlertTriangle,
    className: "border-amber-200 bg-amber-50 text-amber-950",
    accentClassName: "bg-amber-500",
    iconClassName: "text-amber-600",
  },
  error: {
    icon: XCircle,
    className: "border-rose-200 bg-rose-50 text-rose-950",
    accentClassName: "bg-rose-500",
    iconClassName: "text-rose-600",
  },
} as const;

export default function ToastProvider() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const timeoutsRef = useRef(new Map<string, ReturnType<typeof window.setTimeout>>());

  const clearTimeoutFor = useCallback((id: string) => {
    const timeoutId = timeoutsRef.current.get(id);
    if (timeoutId !== undefined) {
      window.clearTimeout(timeoutId);
      timeoutsRef.current.delete(id);
    }
  }, []);

  const dismissToast = useCallback(
    (id: string) => {
      clearTimeoutFor(id);
      setToasts((current) => current.filter((item) => item.id !== id));
    },
    [clearTimeoutFor],
  );

  useEffect(() => {
    const unsubscribe = onToast((payload) => {
      const id = crypto.randomUUID();
      const toast: ToastItem = {
        ...payload,
        id,
        tone: payload.tone ?? "info",
      };

      setToasts((current) => {
        const next = [...current, toast].slice(-MAX_VISIBLE_TOASTS);
        current.filter((item) => !next.includes(item)).forEach((evicted) => clearTimeoutFor(evicted.id));
        return next;
      });

      const timeoutId = window.setTimeout(() => dismissToast(id), TOAST_DURATION_MS);
      timeoutsRef.current.set(id, timeoutId);
    });

    return () => {
      unsubscribe();
      timeoutsRef.current.forEach((timeoutId) => window.clearTimeout(timeoutId));
      timeoutsRef.current.clear();
    };
  }, [clearTimeoutFor, dismissToast]);

  return (
    <div
      aria-live="polite"
      aria-atomic="true"
      className="fixed right-4 top-4 z-[100] flex w-[calc(100%-2rem)] max-w-sm flex-col gap-3 sm:right-6 sm:top-6"
    >
      <AnimatePresence initial={false}>
        {toasts.map((toast) => (
          <Toast key={toast.id} toast={toast} onDismiss={dismissToast} />
        ))}
      </AnimatePresence>
    </div>
  );
}

function Toast({
  toast,
  onDismiss,
}: {
  toast: ToastItem;
  onDismiss: (id: string) => void;
}) {
  const tone = toneStyles[toast.tone];
  const Icon = tone.icon;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: -12, scale: 0.98 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: -8, scale: 0.98 }}
      transition={{ duration: 0.18, ease: "easeOut" }}
      className={`relative flex items-start gap-3 overflow-hidden rounded-lg border p-4 pl-5 shadow-lg shadow-slate-900/10 ${tone.className}`}
    >
      <span className={`absolute inset-y-0 left-0 w-1 ${tone.accentClassName}`} aria-hidden="true" />
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${tone.iconClassName}`} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        <p className="text-sm font-semibold leading-5">{toast.title}</p>
        {toast.description ? (
          <p className="mt-1 text-sm leading-5 opacity-80">{toast.description}</p>
        ) : null}
      </div>
      <button
        type="button"
        onClick={() => onDismiss(toast.id)}
        className="rounded-md p-1 opacity-70 transition hover:bg-black/5 hover:opacity-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-900/30"
        aria-label="Dismiss notification"
      >
        <X className="h-4 w-4" />
      </button>
    </motion.div>
  );
}