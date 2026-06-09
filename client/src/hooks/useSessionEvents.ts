import { useEffect, useCallback } from "react";
import type { ChatMessage, ChatSession } from "@/types/types";
import { useRouter } from "next/navigation";
import { clearAuthState } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import { getChatHistory } from "@/services/chat/chatApi";
import axios from "axios";
import type { UseSessionEventsParams } from "@/types/types";

export function useSessionEvents({
  onLoadSession,
  onNewSession,
}: UseSessionEventsParams): void {
  const router = useRouter();

  const handleLoadSession = useCallback(
    async (event: Event) => {
      const customEvent = event as CustomEvent<ChatSession>;
      const session = customEvent.detail;
      const sessionMessages = session?.messages ?? [];
      const chatToken = session?.chatToken ?? session?.id;

      try {
        let mappedMessages = sessionMessages;

        // Fetch history if we have a valid chat token
        if (chatToken && !chatToken.startsWith("session_")) {
          try {
            const response = await getChatHistory(chatToken);
            mappedMessages = (response.history ?? [])
              .map((m) => {
                const normalizedRole = m.role?.toLowerCase();
                const isUser =
                  normalizedRole === "human" || normalizedRole === "user";
                const role = isUser
                  ? ("user" as const)
                  : ("assistant" as const);

                return {
                  id: m.id ?? crypto.randomUUID(),
                  role,
                  content: (m.msg ?? "")
                    .trim()
                    .replace(/^(human|bot):\s*/i, ""),
                };
              })
              .filter((m) => m.content.length > 0);
          } catch (error) {
            const status = axios.isAxiosError(error)
              ? error.response?.status
              : undefined;
            if (status !== 404) {
              throw error;
            }
          }
        }

        await onLoadSession(session, mappedMessages);
      } catch (error) {
        const status = axios.isAxiosError(error)
          ? error.response?.status
          : undefined;
        if (status === 401) {
          clearAuthState();
          router.push("/");
          return;
        }

        showToast({
          title: "Could not load history",
          description:
            "The saved conversation could not be restored from the server.",
          tone: "error",
        });
      }
    },
    [onLoadSession, router],
  );

  const handleNewSession = useCallback(async () => {
    try {
      await onNewSession();
    } catch (error) {
      const status = axios.isAxiosError(error)
        ? error.response?.status
        : undefined;
      if (status === 401) {
        clearAuthState();
        router.push("/");
        return;
      }

      showToast({
        title: "Could not start chat",
        description: "A new chat session could not be prepared.",
        tone: "error",
      });
    }
  }, [onNewSession, router]);

  useEffect(() => {
    window.addEventListener("chat:load-session", handleLoadSession);
    window.addEventListener("chat:new-session", handleNewSession);

    return () => {
      window.removeEventListener("chat:load-session", handleLoadSession);
      window.removeEventListener("chat:new-session", handleNewSession);
    };
  }, [handleLoadSession, handleNewSession]);
}
