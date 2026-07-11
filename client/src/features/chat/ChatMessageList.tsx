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
                  className={`neu-flat-sm w-fit max-w-[92%] sm:max-w-[80%] lg:max-w-[70%] px-4 py-3`}
                  style={{
                    color: message.role === "user" ? "#c7bcdc" : "#3d2f4d",
                    backgroundColor: message.role === "user" ? "#615676" : "#9489a9",
                  }}
                >
                  <p className="whitespace-pre-wrap break-words text-sm leading-relaxed">
                    {message.content}
                  </p>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>

          {connectionState === "connecting" && messages.length === 0 && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-start"
            >
              <div className="neu-flat-sm w-fit max-w-[92%] sm:max-w-[80%] lg:max-w-[70%] px-4 py-3" style={{ backgroundColor: "#9489a9" }}>
                <div className="flex gap-1">
                  {[0, 0.2, 0.4].map((delay) => (
                    <motion.span
                      key={delay}
                      animate={{ opacity: [0.4, 1, 0.4] }}
                      transition={{ duration: 1.2, repeat: Infinity, delay }}
                      className="h-2 w-2 rounded-full"
                      style={{ backgroundColor: "#615676" }}
                    />
                  ))}
                </div>
              </div>
            </motion.div>
          )}

          {isAssistantTyping && connectionState === "connected" && (
            <div className="flex justify-start">
              <div className="neu-flat-sm w-fit max-w-[92%] sm:max-w-[80%] lg:max-w-[70%] space-y-2 px-4 py-3" style={{ backgroundColor: "#9489a9" }}>
                <div className="h-3 w-32 animate-pulse rounded-full" style={{ backgroundColor: "#7a6b8f" }} />
                <div className="h-3 w-40 animate-pulse rounded-full" style={{ backgroundColor: "#7a6b8f" }} />
                <div className="h-3 w-24 animate-pulse rounded-full" style={{ backgroundColor: "#7a6b8f" }} />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>
    </div>
  );
}
