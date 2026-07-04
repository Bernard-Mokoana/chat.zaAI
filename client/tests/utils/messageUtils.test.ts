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

    it("Edge Case: safely handles missing or malformed fields in the backend response", () => {
      const malformedHistory: Array<{
        id?: string;
        role?: string;
        msg?: string;
      }> = [{ role: "user" }, { msg: "Hello" }];

      const result = normalizeHistoryMessage(malformedHistory);

      expect(result[0].content).toBe("");
      expect(result[1].role).toBeUndefined();
    });
  });
});
