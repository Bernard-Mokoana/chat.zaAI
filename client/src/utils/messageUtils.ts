export const normalizeHistoryMessage = (
  history?: Array<{ id?: string; role?: string; msg?: string }>,
) =>
  (history ?? []).map((m) => {
    const normalizedRole = m.role?.toLowerCase();

    let role: "user" | "assistant" | undefined;
    if (normalizedRole === "human" || normalizedRole === "user") {
      role = "user";
    } else if (normalizedRole !== undefined) {
      role = "assistant";
    }

    return {
      id: m.id ?? crypto.randomUUID(),
      role,
      content: (m.msg ?? "").trim().replace(/^(human|bot):\s*/i, ""),
      timestamp: Date.now(),
    };
  });
