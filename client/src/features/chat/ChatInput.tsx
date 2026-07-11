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
    <form onSubmit={handleSubmit} className="neu-flat-sm w-full" style={{ borderRadius: "40px 40px 0 0", borderBottomLeftRadius: "0", borderBottomRightRadius: "0" }}>
      <div className="mx-auto w-full px-4 py-4 sm:px-6">
        <div className="flex flex-col gap-3 sm:gap-2 sm:flex-row sm:items-center">
          <input
            type="text"
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={placeholder}
            disabled={disabled}
            className="neu-inset flex-1 px-4 py-3 text-sm outline-none transition-all placeholder-opacity-60 disabled:opacity-60 disabled:cursor-not-allowed"
            style={{ color: "#3d2f4d" }}
          />
          <button
            type="submit"
            disabled={!value.trim() || disabled}
            className="neu-btn w-full sm:w-auto flex items-center justify-center gap-2 px-6 py-3 text-sm font-medium"
            style={{ color: "#3d2f4d" }}
          >
            <Send className="h-4 w-4" />
            <span className="hidden sm:inline">Send</span>
          </button>
        </div>
      </div>
    </form>
  );
}
