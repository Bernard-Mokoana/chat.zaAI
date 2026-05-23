import type { ChatSessionResponse } from "@/types/types";
import { httpClient } from "../httpClient";
import { getAccessToken } from "../storage/chatStorage";

export async function createChatSession(
  name: string,
): Promise<ChatSessionResponse> {
  const token = getAccessToken();

  if (!token) {
    throw new Error("Access token is required to create a chat session");
  }

  const response = await httpClient.post<ChatSessionResponse>(
    "/api/v1/chat/token",
    null,
    {
      params: { name },
    },
  );

  return response.data;
}

export async function refreshChatSession(
  token: string,
): Promise<ChatSessionResponse> {
  const response = await httpClient.get<ChatSessionResponse>(
    "/api/v1/chat/refresh_token",
    {
      params: { token },
    },
  );

  return response.data;
}
