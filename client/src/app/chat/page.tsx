"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import ChatPanel from "@/features/chat/ChatPanel";
import { refreshAccessToken } from "@/services/auth/authApi";
import {clearAuthState, getAccessToken, getAuthUser } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";

export default function ChatPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function authorizeChat() {
      const accessToken = getAccessToken();
      const authUser = getAuthUser();

      if (accessToken && authUser) {
        if (alive) setDisplayName(authUser.name);
        return;
      }

      try {
        const auth = await refreshAccessToken();

        if (alive) setDisplayName(auth.user.name);
      } catch {
        clearAuthState();
        if (alive) {
          showToast({
            title: "Sign in again",
            description: "Your session expired. Please sign in to continue.",
            tone: "warning",
          });
          router.push("/");
        }
      }
    }

    authorizeChat();

    return () => {
      alive = false;
    };
  }, [router]);

  if (!displayName) {
    return null; // both server and client agree on this initial render
  }

  return (
    <main style={{ minHeight: "100vh" }}>
      <Suspense fallback={<div>Loading...</div>}>
        <ChatPanel displayName={displayName} />
      </Suspense>
    </main>
  );
}
