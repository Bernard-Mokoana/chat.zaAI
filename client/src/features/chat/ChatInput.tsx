"use client";

import { Send } from "lucide-react";
import { useCallback } from "react";
import type { FormEvent } from "react";
import type { ChatInputProps } from "@/types/types";


export default function ChatInput({
  value,
  onChange,
  onSubmit,
  disabled = false,
  placeholder = "Type your message...",
}: ChatInputProps) {
  const handleSubmit = useCallback(
    (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      onSubmit(event);
    },
    [onSubmit]
  );

  return (
    <form onSubmit={handleSubmit} className="w-full border-t border-slate-200 bg-white">
      <div className="mx-auto w-full px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-3 sm:gap-2 sm:flex-row sm:items-center">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            className="w-full flex-1 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm placeholder-slate-500 outline-none transition-all focus:border-transparent focus:ring-2 focus:ring-blue-500 disabled:opacity-60 disabled:cursor-not-allowed"
          />
          <button
            type="submit"
            disabled={!value.trim() || disabled}
            className="w-full sm:w-auto flex items-center justify-center gap-2 rounded-xl bg-blue-600 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>
    </form>
  );
}
