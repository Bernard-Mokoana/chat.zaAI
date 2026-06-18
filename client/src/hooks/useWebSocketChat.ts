import { useCallback, useRef, useState } from "react";
import type { ChatSocket } from "@/services/ws/chatSocket";
import type { ChatSocketParams } from "@/types/types";
import { createChatSocket } from "@/services/ws/chatSocket";
import { getAccessToken } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import type { ConnectionState, UseWebSocketChatReturn } from "@/types/types";

const WS_RATE_LIMIT_MESSAGE = "Too many messages.";

export function useWebSocketChat(): UseWebSocketChatReturn {
  const socketRef = useRef<ChatSocket | null>(null);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("connecting");

  const suppressedSocketsRef = useRef<WeakSet<ChatSocket>>(new WeakSet());

  const connect = useCallback(
    (chatToken: string, onMessage: (msg: string) => void) => {
      const accessToken = getAccessToken();

      if (!accessToken) {
        setConnectionState("error");
        showToast({
          title: "Authentication error",
          description: "Access token is required to connect to chat",
          tone: "error",
        });
        return;
      }

      if (socketRef.current) {
        const previousSocket = socketRef.current;
        suppressedSocketsRef.current.add(previousSocket);
        previousSocket.disconnect();
      }

      let socket: ChatSocket | undefined;

      const params: ChatSocketParams = {
        accessToken,
        chatToken,
        onOpen: () => setConnectionState("connected"),
        onClose: () => {
          if (socket && suppressedSocketsRef.current.has(socket)) {
            suppressedSocketsRef.current.delete(socket);
            return;
          }

          setConnectionState("disconnected");
          showToast({
            title: "Chat disconnected",
            description: "Messages pause until the connection is restored.",
            tone: "warning",
          });
        },
        onError: () => {
          setConnectionState("error");
          showToast({
            title: "Chat connection problem",
            description: "The live chat connection could not stay open.",
            tone: "error",
          });
        },
        onMessage: (message: string) => {
          if (message.startsWith(WS_RATE_LIMIT_MESSAGE)) {
            showToast({
              title: "Message limit reached",
              description:
                "Please wait a moment before sending another message.",
              tone: "warning",
            });
            return;
          }

          onMessage(message);
        },
      };

      socket = createChatSocket(params);
      socketRef.current = socket;
    },
    [],
  );

  const disconnect = useCallback(() => {
    const socket = socketRef.current;
    if (socket) {
      suppressedSocketsRef.current.add(socket);
      socket.disconnect();
      socketRef.current = null;
      setConnectionState("disconnected");
    }
  }, []);

  return {
    connectionState,
    isConnected: connectionState === "connected",
    connect,
    disconnect,
  };
}
