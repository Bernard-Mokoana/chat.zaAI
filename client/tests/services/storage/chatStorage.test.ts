import {
  setChatToken,
  getChatToken,
  clearChatToken,
} from "@/services/storage/chatStorage";

describe("Chat Storage Service", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.sessionStorage.clear();
  });

  it("successfully saves and retrieves a chat session token", () => {
    const mockChatToken = "chat-uuid-12345";

    setChatToken(mockChatToken);
    const retrievedToken = getChatToken();

    expect(retrievedToken).toBe(mockChatToken);
  });

  it("returns null when attempting to retrieve a non-existent token", () => {
    const retrievedToken = getChatToken();

    expect(retrievedToken).toBeNull();
  });

  it("successfully clears the chat token from storage", () => {
    setChatToken("temporary-chat-token");

    clearChatToken();
    const retrievedToken = getChatToken();

    expect(retrievedToken).toBeNull();
  });
});
