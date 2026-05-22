"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter } from "next/navigation";
import ChatPanel from "@/features/chat/ChatPanel";
import { getChatName } from "@/services/storage/chatStorage";

export default function ChatPage() {
  const router = useRouter();
  const [displayName, setDisplayName] = useState<string | null>(null);

  useEffect(() => {
    const name = getChatName();
    if (!name) {
      router.push("/");
      return;
    }

    const timeoutId = window.setTimeout(() => {
      setDisplayName(name);
    }, 0);

    return () => window.clearTimeout(timeoutId);
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
