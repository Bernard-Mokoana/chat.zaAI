import { httpClient } from "../httpClient";
import { getAccessToken } from "../storage/chatStorage";

export async function createChatSession(name: string) {
  const token = getAccessToken();

  const response = await httpClient.post("/api/v1/chat/token", null, {
    params: { name },
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  return response.data;
}

export async function refreshChatSession(token: string) {
  const response = await httpClient.get("/api/v1/chat/refresh_token", {
    params: { token },
  });
  return response.data;
}
