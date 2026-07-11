"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import ChatPanel from "@/features/chat/ChatPanel";
import { refreshAccessToken } from "@/services/auth/authApi";
import {clearAuthState, getAccessToken, getAuthUser } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import { isTokenExpired } from "@/utils/isTokenExpired";
export default function ChatPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;

    async function authorizeChat() {
      const accessToken = getAccessToken();
      const authUser = getAuthUser();

      if (accessToken && authUser && !isTokenExpired(accessToken)) {
        if (alive) setDisplayName(authUser.name);
        return;
      }

      try {
        const auth = await refreshAccessToken();
        if (alive) setDisplayName(auth.user.name);
      } catch {
        if (alive) {
          clearAuthState();
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

  if (!displayName) return null;

  return (
    <main style={{ minHeight: "100vh", backgroundColor: "#9489a9" }}>
      <Suspense fallback={<div>Loading...</div>}>
        <ChatPanel displayName={displayName} />
      </Suspense>
    </main>
  );
}
