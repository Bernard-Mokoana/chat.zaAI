import { createChatSession, getChatHistory } from "@/services/chat/chatApi";
import { httpClient } from "@/services/httpClient";

jest.mock("@/services/httpClient");
const mockedHttpClient = httpClient as jest.Mocked<typeof httpClient>;

describe("Chat API Service", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe("generateChatToken", () => {
    it("successfully generates a chat token based on the provided name", async () => {
      const mockResponse = { data: { token: "new-chat-token-uuid" } };
      mockedHttpClient.post.mockResolvedValueOnce(mockResponse);

      const result = await createChatSession("System Design Prompt");

      expect(mockedHttpClient.post).toHaveBeenCalledWith(
        "/api/v1/chat/token",
        null,
        { params: { name: "System Design Prompt" } },
      );
      expect(result).toBe(mockResponse.data);
    });
  });

  describe("getChatHistory", () => {
    it("successfully retrieves the chat history for a specific token", async () => {
      const mockResponse = {
        data: { status: "success", history: [{ role: "user", content: "Hi" }] },
      };
      mockedHttpClient.get.mockResolvedValueOnce(mockResponse);

      const result = await getChatHistory("existing-chat-token-uuid");

      expect(mockedHttpClient.get).toHaveBeenCalledWith(
        "/api/v1/chat/history",
        { headers: { "X-Chat-Token": "existing-chat-token-uuid" } },
      );
      expect(result).toBe(mockResponse.data);
    });
  });
});
