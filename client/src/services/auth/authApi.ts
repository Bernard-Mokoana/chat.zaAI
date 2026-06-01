import { httpClient } from "../httpClient";
import type { AuthResponse } from "@/types/types";
import {
  clearAuthState,
  setAccessToken,
  setAuthUser,
} from "../storage/chatStorage";

export async function login(payload: { email: string; password: string }) {
  const response = await httpClient.post<AuthResponse>(
    "/api/v1/auth/login",
    payload,
  );
  return response.data;
}

export async function register(payload: {
  name: string;
  email: string;
  password: string;
}) {
  const response = await httpClient.post<AuthResponse>(
    "/api/v1/auth/register",
    payload,
  );
  return response.data;
}

export async function logout() {
  const response = await httpClient.post("/api/v1/auth/logout");
  clearAuthState();
  return response.data;
}

export async function refreshAccessToken() {
  const response = await httpClient.post<AuthResponse>("/api/v1/auth/refresh");
  setAccessToken(response.data.access_token);
  setAuthUser(response.data.user);
  return response.data;
}
