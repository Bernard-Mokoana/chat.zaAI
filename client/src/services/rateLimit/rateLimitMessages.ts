import type { RateLimitResponse } from "@/types/types";

export function getRateLimitTitle(scope?: string) {
  if (scope === "auth") return "Too many sign-in attempts";
  if (scope === "chat_session") return "Too many chat session requests";
  if (scope === "api") return "You are sending requests too quickly";
  return "Too many requests";
}

export function getRateLimitDescription(
  payload?: RateLimitResponse,
  retryAfterHeader?: string,
) {
  const retryAfter =
    payload?.rate_limit?.retry_after ?? Number(retryAfterHeader);
  const waitText =
    Number.isFinite(retryAfter) && retryAfter > 0
      ? ` Try again in about ${Math.ceil(retryAfter)} seconds.`
      : " Please wait a moment before trying again.";

  return `${payload?.detail ?? "The server is slowing requests to keep the chat stable."}${waitText}`;
}

export function getRateLimitInlineMessage(
  payload?: RateLimitResponse,
  retryAfterHeader?: string,
) {
  return `${getRateLimitTitle(payload?.rate_limit?.scope)}. ${getRateLimitDescription(
    payload,
    retryAfterHeader,
  )}`;
}
