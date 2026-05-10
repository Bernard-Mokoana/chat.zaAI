import axios from "axios";
import { getAccessToken } from "./storage/chatStorage";

const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_URL?.trim() || "http://localhost:3500";

export const httpClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

httpClient.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
