import { httpClient } from "../httpClient";
import type { AuthResponse } from "@/types/types";

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
  return response.data;
}
