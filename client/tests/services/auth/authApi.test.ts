import { httpClient } from "@/services/httpClient";
import { login, register, logout } from "@/services/auth/authApi";

jest.mock("@/services/httpClient");

const mockedHttpClient = httpClient as jest.Mocked<typeof httpClient>;

describe("Auth API Service", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("login()", () => {
    it("Happy Path: successfully logs in and returns user data", async () => {
      const mockResponse = {
        data: {
          access_token: "fake-jwt-token",
          user: { id: "123", email: "bernard@example.com" },
        },
      };
      mockedHttpClient.post.mockResolvedValueOnce(mockResponse);

      const credentials = {
        email: "bernard@example.com",
        password: "securePassword123",
      };

      const result = await login(credentials);

      expect(mockedHttpClient.post).toHaveBeenCalledTimes(1);
      expect(mockedHttpClient.post).toHaveBeenCalledWith(
        "/api/v1/auth/login",
        credentials,
      );
      expect(result).toEqual(mockResponse.data);
    });

    it("Error Condition: throws a clean error message when the API rejects the credentials", async () => {
      const mockError = {
        response: { data: { detail: "Invalid email or password" } },
      };
      mockedHttpClient.post.mockRejectedValueOnce(mockError);

      await expect(
        login({ email: "bernard@example.com", password: "wrong" }),
      ).rejects.toEqual(mockError);
    });
  });

  describe("register()", () => {
    it("Happy Path: successfully registers a new user", async () => {
      const mockResponse = {
        data: { message: "Registration successful. Please verify your email." },
      };
      mockedHttpClient.post.mockResolvedValueOnce(mockResponse);

      const newUser = {
        name: "Bernard",
        email: "bernard@example.com",
        password: "securePassword",
      };

      const result = await register(newUser);

      expect(mockedHttpClient.post).toHaveBeenCalledWith(
        "/api/v1/auth/register",
        newUser,
      );
      expect(result).toEqual(mockResponse.data);
    });
  });

  describe("logout()", () => {
    it("Happy Path: calls the logout endpoint successfully", async () => {
      mockedHttpClient.post.mockResolvedValueOnce({
        data: { message: "Logged out" },
      });

      await logout();

      expect(mockedHttpClient.post).toHaveBeenCalledWith("/api/v1/auth/logout");
    });
  });
});
