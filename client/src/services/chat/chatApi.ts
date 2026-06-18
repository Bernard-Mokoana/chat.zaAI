import type { ChatHistoryResponse, ChatSessionResponse } from "@/types/types";
import { httpClient } from "../httpClient";

export async function createChatSession(
  name: string,
): Promise<ChatSessionResponse> {
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
      headers: { "X-Chat-Token": token },
    },
  );

  return response.data;
}

export async function getChatHistory(
  token: string,
): Promise<ChatHistoryResponse> {
  const response = await httpClient.get<ChatHistoryResponse>(
    `/api/v1/chat/history`,
    {
      headers: { "X-Chat-Token": token },
    },
  );

  return response.data;
}
