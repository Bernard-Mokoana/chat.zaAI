import {
  loadSessions,
  saveSession,
  deleteSession,
  getActiveSessionId,
  setActiveSessionId,
  createSession,
} from "@/services/storage/sessionStorage";
import { ChatMessage } from "@/types/types";

describe("Session Storage Service", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  describe("loadSessions & saveSession", () => {
    it("Happy Path: saves a new session and loads it correctly", () => {
      const newSession = createSession();

      saveSession(newSession);
      const sessions = loadSessions();

      expect(sessions).toHaveLength(1);
      expect(sessions[0].id).toBe(newSession.id);
    });

    it("Happy Path: updates an existing session instead of duplicating it", () => {
      const session = createSession();
      saveSession(session);

      const updatedSession = { ...session, title: "Updated Title" };
      saveSession(updatedSession);

      const sessions = loadSessions();
      expect(sessions).toHaveLength(1);
      expect(sessions[0].title).toBe("Updated Title");
    });

    it("Edge Case: returns an empty array if localStorage is empty or corrupted", () => {
      expect(loadSessions()).toEqual([]);

      localStorage.setItem("chat_sessions", "{ invalid JSON ]");
      expect(loadSessions()).toEqual([]);
    });
  });

  describe("deleteSession", () => {
    it("Happy Path: removes a specific session by ID", () => {
      const session1 = createSession();
      const session2 = createSession();
      saveSession(session1);
      saveSession(session2);

      deleteSession(session1.id);

      const sessions = loadSessions();
      expect(sessions).toHaveLength(1);
      expect(sessions[0].id).toBe(session2.id);
    });
  });

  describe("Active Session ID", () => {
    it("Happy Path: sets and gets the active session ID", () => {
      setActiveSessionId("active-123");
      expect(getActiveSessionId()).toBe("active-123");
    });

    it("Happy Path: clears the active session when passed null", () => {
      setActiveSessionId("active-123");
      setActiveSessionId(null);
      expect(getActiveSessionId()).toBeNull();
    });
  });

  describe("createSession", () => {
    it("Happy Path: generates a default session when no initial message is provided", () => {
      const session = createSession();
      expect(session.id).toBeDefined();
      expect(session.title).toBe("New conversation");
      expect(session.messages).toEqual([]);
    });

    it("Happy Path: bases the title and preview off the first provided message", () => {
      const mockMsg: ChatMessage = {
        id: "1",
        role: "user",
        content: "What is the speed of light?",
      };

      const session = createSession(mockMsg, "custom-token-123");

      expect(session.chatToken).toBe("custom-token-123");
      expect(session.title).toBe("What is the speed of light?");
      expect(session.preview).toBe("What is the speed of light?");
      expect(session.messages).toHaveLength(1);
    });
  });
});
