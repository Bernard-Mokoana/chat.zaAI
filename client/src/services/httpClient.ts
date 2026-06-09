import axios, {
  AxiosError,
  AxiosHeaders,
  InternalAxiosRequestConfig,
  AxiosResponse,
} from "axios";
import {
  clearAuthState,
  getAccessToken,
  setAccessToken,
  setAuthUser,
} from "./storage/chatStorage";
import {
  getRateLimitDescription,
  getRateLimitTitle,
} from "./rateLimit/rateLimitMessages";
import { showToast } from "./toast/toastEvents";
import type { AuthResponse, RateLimitResponse } from "@/types/types";

const apiBaseUrl: string =
  process.env.NEXT_PUBLIC_API_URL?.trim() || "http://localhost:3501";

export const httpClient = axios.create({
  baseURL: apiBaseUrl,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

export type RetriableRequestConfig = InternalAxiosRequestConfig & {
  _retry?: boolean;
};

let refreshPromise: Promise<AuthResponse> | null = null;

function shouldSkipRefresh(url?: string): boolean {
  return (
    !url ||
    url.includes("/api/v1/auth/login") ||
    url.includes("/api/v1/auth/register") ||
    url.includes("/api/v1/auth/refresh")
  );
}

async function refreshAccessToken(): Promise<AuthResponse> {
  if (!refreshPromise) {
    refreshPromise = axios
      .post<AuthResponse>(`${apiBaseUrl}/api/v1/auth/refresh`, null, {
        withCredentials: true,
        headers: {
          "Content-Type": "application/json",
        },
      })
      .then((response: AxiosResponse<AuthResponse>) => {
        setAccessToken(response.data.access_token);
        setAuthUser(response.data.user);
        return response.data;
      })
      .catch((error: AxiosError) => {
        clearAuthState();
        throw error;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }

  return refreshPromise;
}

httpClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

httpClient.interceptors.response.use(
  (response: AxiosResponse) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as RetriableRequestConfig | undefined;
    const status = error.response?.status;

    if (status === 429) {
      const payload = error.response?.data as RateLimitResponse | undefined;
      const retryAfter = error.response?.headers["retry-after"] as
        | string
        | undefined;

      showToast({
        title: getRateLimitTitle(payload?.rate_limit?.scope),
        description: getRateLimitDescription(payload, retryAfter),
        tone: "warning",
      });

      return Promise.reject(error);
    }

    if (
      status !== 401 ||
      !originalRequest ||
      originalRequest._retry ||
      shouldSkipRefresh(originalRequest.url)
    ) {
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      const auth = await refreshAccessToken();
      const headers = AxiosHeaders.from(originalRequest.headers);
      headers.set("Authorization", `Bearer ${auth.access_token}`);
      originalRequest.headers = headers;

      return httpClient(originalRequest);
    } catch (refreshError) {
      return Promise.reject(refreshError);
    }
  },
);
