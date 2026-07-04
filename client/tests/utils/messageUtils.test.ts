import { normalizeHistoryMessage } from "@/utils/messageUtils";

describe("Message Utils", () => {
  describe("normalizeHistoryMessage", () => {
    it("Happy Path: converts backend history format into frontend ChatMessage format", () => {
      const mockRawHistory = [
        { role: "user", msg: "What is the capital of France?" },
        { role: "assistant", msg: "The capital of France is Paris." },
      ];

      const result = normalizeHistoryMessage(mockRawHistory);

      expect(result).toHaveLength(2);

      expect(result[0].role).toBe("user");
      expect(result[0].content).toBe("What is the capital of France?");
      expect(typeof result[0].id).toBe("string");
      expect(typeof result[0].timestamp).toBe("number");

      expect(result[1].role).toBe("assistant");
      expect(result[1].content).toBe("The capital of France is Paris.");
    });

    it("Edge Case: returns an empty array if given an empty array", () => {
      const result = normalizeHistoryMessage([]);
      expect(result).toEqual([]);
    });

    it("Edge Case: returns an empty array if given undefined", () => {
      const result = normalizeHistoryMessage(undefined);
      expect(result).toEqual([]);
    });

    it("Edge Case: safely handles missing or malformed fields in the backend response", () => {
      const malformedHistory: Array<{
        id?: string;
        role?: string;
        msg?: string;
      }> = [{ role: "user" }, { msg: "Hello" }];

      const result = normalizeHistoryMessage(malformedHistory);

      expect(result[0].role).toBe("user");
      expect(result[0].content).toBe("");

      // No role provided -> defaults to "assistant" rather than undefined
      expect(result[1].role).toBe("assistant");
      expect(result[1].content).toBe("Hello");
    });

    it("Edge Case: defaults role to 'assistant' when role is missing or unrecognized", () => {
      const result = normalizeHistoryMessage([
        { msg: "no role here" },
        { role: "bot", msg: "unrecognized role" },
        { role: "HUMAN", msg: "case-insensitive user role" },
      ]);

      expect(result[0].role).toBe("assistant");
      expect(result[1].role).toBe("assistant");
      expect(result[2].role).toBe("user");
    });

    it("Edge Case: normalizes role case-insensitively", () => {
      const result = normalizeHistoryMessage([
        { role: "USER", msg: "shouting user" },
        { role: "Assistant", msg: "mixed case assistant" },
        { role: "Human", msg: "mixed case human" },
      ]);

      expect(result[0].role).toBe("user");
      expect(result[1].role).toBe("assistant");
      expect(result[2].role).toBe("user");
    });

    it("Edge Case: strips 'human:' and 'bot:' prefixes from message content", () => {
      const result = normalizeHistoryMessage([
        { role: "user", msg: "human: Hello there" },
        { role: "assistant", msg: "bot: Hi, how can I help?" },
        { role: "assistant", msg: "BOT: case-insensitive prefix" },
      ]);

      expect(result[0].content).toBe("Hello there");
      expect(result[1].content).toBe("Hi, how can I help?");
      expect(result[2].content).toBe("case-insensitive prefix");
    });

    it("Edge Case: trims whitespace from message content", () => {
      const result = normalizeHistoryMessage([
        { role: "user", msg: "   padded message   " },
      ]);

      expect(result[0].content).toBe("padded message");
    });

    it("Edge Case: generates a fallback id when id is missing", () => {
      const result = normalizeHistoryMessage([
        { role: "user", msg: "no id provided" },
      ]);

      expect(typeof result[0].id).toBe("string");
      expect(result[0].id.length).toBeGreaterThan(0);
    });

    it("Edge Case: preserves provided id when present", () => {
      const result = normalizeHistoryMessage([
        { id: "msg-123", role: "user", msg: "has an id" },
      ]);

      expect(result[0].id).toBe("msg-123");
    });
  });
});
