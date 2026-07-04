export const normalizeHistoryMessage = (
  history?: Array<{ id?: string; role?: string; msg?: string }>,
) =>
  (history ?? []).map((m) => {
    const normalizedRole = m.role?.toLowerCase();

    const role: "user" | "assistant" =
      normalizedRole === "human" || normalizedRole === "user"
        ? "user"
        : "assistant";

    return {
      id: m.id ?? crypto.randomUUID(),
      role,
      content: (m.msg ?? "").trim().replace(/^(human|bot):\s*/i, ""),
      timestamp: Date.now(),
    };
  });
