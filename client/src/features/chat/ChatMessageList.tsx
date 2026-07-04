"use client";

import { AnimatePresence, motion } from "motion/react";
import { useEffect, useRef } from "react";
import type { ChatMessageListProps } from "@/types/types";


export default function ChatMessageList({
  messages,
  connectionState,
  isAssistantTyping,
}: ChatMessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to latest message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isAssistantTyping]);

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="mx-auto w-full px-4 py-6 sm:px-6">
        <div className="space-y-4">
          <AnimatePresence initial={false}>
            {messages.map((message) => (
              <motion.div
                key={message.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                transition={{ duration: 0.25 }}
                className={`flex ${
                  message.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                <div
                  className={`w-fit max-w-[92%] sm:max-w-[80%] lg:max-w-[70%] rounded-2xl px-4 py-3 shadow-sm ${
                    message.role === "user"
                      ? "bg-blue-600 text-white"
                      : "border border-slate-200 bg-white text-slate-900"
                  }`}
                >
                  <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {message.content}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {/* Connection state indicator */}
          {connectionState === "connecting" && messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="w-fit max-w-[92%] sm:max-w-[80%] lg:max-w-[70%] rounded-2xl border border-slate-200 bg-white px-4 py-3">
                <div className="flex gap-1">
                  {[0, 0.2, 0.4].map((delay) => (
                    <motion.span
                      key={delay}
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay }}
                      className="h-2 w-2 rounded-full bg-slate-400"
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {/* Typing indicator */}
          {isAssistantTyping && connectionState === "connected" && (
            <div className="flex justify-start">
              <div className="w-fit max-w-[92%] sm:max-w-[80%] lg:max-w-[70%] space-y-2 rounded-2xl border border-slate-200 bg-white px-4 py-3">
                <div className="h-3 w-32 animate-pulse rounded-full bg-slate-200" />
                <div className="h-3 w-40 animate-pulse rounded-full bg-slate-200" />
                <div className="h-3 w-24 animate-pulse rounded-full bg-slate-200" />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}
