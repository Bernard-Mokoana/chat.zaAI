import type { ChatSession } from "@/types/types";

export function relativeTime(ts: number): string {
  const diff = Date.now() - ts;
  const mins = Math.floor(diff / 60_000);
  const hours = Math.floor(diff / 3_600_000);
  const days = Math.floor(diff / 86_400_000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (hours < 24) return `${hours}h ago`;
  if (days < 7) return `${days}d ago`;
  return new Date(ts).toLocaleDateString();
}

export function groupSessions(sessions: ChatSession[]) {
  const now = Date.now();
  const today: ChatSession[] = [];
  const yesterday: ChatSession[] = [];
  const older: ChatSession[] = [];

  for (const s of sessions) {
    const diff = now - s.updatedAt;
    if (diff < 86_400_000) today.push(s);
    else if (diff < 172_800_000) yesterday.push(s);
    else older.push(s);
  }

  return { today, yesterday, older };
}
