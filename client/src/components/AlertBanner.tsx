"use client";

import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import type { AlertTone, AlertBannerProps } from "@/types/types";


const toneStyles: Record<AlertTone, { icon: typeof Info; className: string; iconClassName: string }> = {
  success: {
    icon: CheckCircle2,
    className: "border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-900/30 dark:bg-emerald-950/20 dark:text-emerald-400",
    iconClassName: "text-emerald-600 dark:text-emerald-400",
  },
  error: {
    icon: XCircle,
    className: "border-rose-200 bg-rose-50 text-rose-700 dark:border-rose-900/30 dark:bg-rose-950/20 dark:text-rose-400",
    iconClassName: "text-rose-600 dark:text-rose-400",
  },
  info: {
    icon: Info,
    className: "border-sky-200 bg-sky-50 text-sky-800 dark:border-sky-900/30 dark:bg-sky-950/20 dark:text-sky-400",
    iconClassName: "text-sky-600 dark:text-sky-400",
  },
  warning: {
    icon: AlertTriangle,
    className: "border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-900/30 dark:bg-amber-950/20 dark:text-amber-400",
    iconClassName: "text-amber-600 dark:text-amber-400",
  },
};

export default function AlertBanner({ tone, message, onDismiss }: AlertBannerProps) {
  const style = toneStyles[tone];
  const Icon = style.icon;

  return (
    <div className={`flex items-start gap-3 rounded-lg border p-4 text-sm ${style.className}`}>
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${style.iconClassName}`} />
      <p className="flex-1">{message}</p>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-md p-1 opacity-70 transition hover:bg-black/5 hover:opacity-100"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
