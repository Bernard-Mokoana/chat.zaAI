export const normalizeHistoryMessage = (
  history?: Array<{ id?: string; role?: string; msg?: string }>,
) =>
  (history ?? [])
    .map((m) => {
      const normalizedRole = m.role?.toLowerCase();
      const isUser = normalizedRole === "human" || normalizedRole === "user";
      const role = isUser ? ("user" as const) : ("assistant" as const);

      return {
        id: m.id ?? crypto.randomUUID(),
        role,
        content: (m.msg ?? "").trim().replace(/^(human|bot):\s*/i, ""),
      };
    })
    .filter((m) => m.content.length > 0);
