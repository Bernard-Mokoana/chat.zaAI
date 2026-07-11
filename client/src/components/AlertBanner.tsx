"use client";

import { AlertTriangle, CheckCircle2, Info, X, XCircle } from "lucide-react";
import type { AlertTone, AlertBannerProps } from "@/types/types";


const toneStyles: Record<AlertTone, { icon: typeof Info; className: string; iconClassName: string }> = {
  success: {
    icon: CheckCircle2,
    className: "border-emerald-700/40 bg-emerald-900/30 text-emerald-300",
    iconClassName: "text-emerald-400",
  },
  error: {
    icon: XCircle,
    className: "border-rose-700/40 bg-rose-900/30 text-rose-300",
    iconClassName: "text-rose-400",
  },
  info: {
    icon: Info,
    className: "border-sky-700/40 bg-sky-900/30 text-sky-300",
    iconClassName: "text-sky-400",
  },
  warning: {
    icon: AlertTriangle,
    className: "border-amber-700/40 bg-amber-900/30 text-amber-300",
    iconClassName: "text-amber-400",
  },
};

export default function AlertBanner({ tone, message, onDismiss }: AlertBannerProps) {
  const style = toneStyles[tone];
  const Icon = style.icon;

  return (
    <div className={`card-sm flex items-start gap-3 p-4 text-sm ${style.className}`}>
      <Icon className={`mt-0.5 h-5 w-5 shrink-0 ${style.iconClassName}`} />
      <p className="flex-1">{message}</p>
      {onDismiss && (
        <button
          type="button"
          onClick={onDismiss}
          className="rounded-md p-1 opacity-70 transition hover:bg-white/10 hover:opacity-100 card-sm"
          aria-label="Dismiss"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
