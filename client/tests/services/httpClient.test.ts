import axios from "axios";
import { httpClient } from "@/services/httpClient";
import * as chatStorage from "@/services/storage/chatStorage";
import * as toastEvents from "@/services/toast/toastEvents";

jest.mock("axios", () => {
  const originalAxios = jest.requireActual("axios");
  const mockAxiosInstance = jest.fn() as any;
  mockAxiosInstance.interceptors = {
    request: { use: jest.fn() },
    response: { use: jest.fn() },
  };
  mockAxiosInstance.request = jest.fn();
  const mockAxios = jest.fn(() => mockAxiosInstance) as any;
  mockAxios.create = jest.fn(() => mockAxiosInstance);
  mockAxios.post = jest.fn();
  mockAxios.AxiosHeaders = originalAxios.AxiosHeaders;
  return mockAxios;
});

jest.mock("@/services/storage/chatStorage");
jest.mock("@/services/toast/toastEvents");

describe("HTTP Client Interceptors", () => {
  let requestInterceptor: Function;
  let responseSuccessInterceptor: Function;
  let responseErrorInterceptor: Function;

  beforeAll(() => {
    requestInterceptor = (httpClient.interceptors.request.use as jest.Mock).mock
      .calls[0][0];
    responseSuccessInterceptor = (
      httpClient.interceptors.response.use as jest.Mock
    ).mock.calls[0][0];
    responseErrorInterceptor = (
      httpClient.interceptors.response.use as jest.Mock
    ).mock.calls[0][1];
  });

  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("Request Interceptor", () => {
    it("attaches the Authorization header if a token exists", () => {
      (chatStorage.getAccessToken as jest.Mock).mockReturnValue(
        "valid-jwt-token",
      );

      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBe("Bearer valid-jwt-token");
    });

    it("does not attach the Authorization header if no token exists", () => {
      (chatStorage.getAccessToken as jest.Mock).mockReturnValue(null);

      const config = { headers: {} };
      const result = requestInterceptor(config);

      expect(result.headers.Authorization).toBeUndefined();
    });
  });

  describe("Response Interceptor (Success)", () => {
    it("passes successful responses through untouched", () => {
      const mockResponse = { data: "Success data", status: 200 };
      const result = responseSuccessInterceptor(mockResponse);
      expect(result).toBe(mockResponse);
    });
  });
  describe("Response Interceptor (Error)", () => {
    it("triggers a toast warning for 429 Rate Limit errors and rejects the promise", async () => {
      const mockError = {
        response: {
          status: 429,
          data: { rate_limit: { scope: "api" } },
          headers: { "retry-after": "60" },
        },
      };

      await expect(responseErrorInterceptor(mockError)).rejects.toBe(mockError);

      expect(toastEvents.showToast).toHaveBeenCalledWith(
        expect.objectContaining({
          tone: "warning",
          title: expect.any(String),
        }),
      );
    });

    it("rejects errors other than 401 immediately without refreshing", async () => {
      const mockError = {
        response: { status: 500 },
        config: { url: "/api/v1/chat/history" },
      };
      await expect(responseErrorInterceptor(mockError)).rejects.toBe(mockError);
    });

    it("skips token refresh for auth endpoints (login, register, refresh)", async () => {
      const mockError = {
        response: { status: 401 },
        config: { url: "/api/v1/auth/login" },
      };
      await expect(responseErrorInterceptor(mockError)).rejects.toBe(mockError);
    });

    it("Happy Path: successfully refreshes a 401 and retries the original request", async () => {
      const mockOriginalConfig = {
        url: "/api/v1/chat/history",
        headers: new axios.AxiosHeaders(),
      };
      const mockError = {
        response: { status: 401 },
        config: mockOriginalConfig,
      };

      const mockRefreshResponse = {
        data: { access_token: "new-fresh-token", user: { id: "123" } },
      };
      (axios.post as jest.Mock).mockResolvedValueOnce(mockRefreshResponse);

      const mockFinalData = { data: "Chat History" };
      (httpClient as unknown as jest.Mock).mockResolvedValueOnce(mockFinalData);

      const result = await responseErrorInterceptor(mockError);

      expect(chatStorage.setAccessToken).toHaveBeenCalledWith(
        "new-fresh-token",
      );
      expect(chatStorage.setAuthUser).toHaveBeenCalledWith({ id: "123" });

      expect(mockOriginalConfig.headers.get("Authorization")).toBe(
        "Bearer new-fresh-token",
      );
      expect(httpClient).toHaveBeenCalledWith(mockOriginalConfig);

      expect(result).toBe(mockFinalData);
    });

    it("clears auth state and rejects if the refresh token API call fails", async () => {
      const mockOriginalConfig = { url: "/api/v1/chat/history" };
      const mockError = {
        response: { status: 401 },
        config: mockOriginalConfig,
      };

      const refreshError = new Error("Refresh token invalid");
      (axios.post as jest.Mock).mockRejectedValueOnce(refreshError);

      await expect(responseErrorInterceptor(mockError)).rejects.toBe(
        refreshError,
      );

      expect(chatStorage.clearAuthState).toHaveBeenCalledTimes(1);
    });
  });
});
