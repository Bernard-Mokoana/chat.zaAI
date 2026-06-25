import { isTokenExpired } from "@/utils/isTokenExpired";

describe("isTokenExpired Utility", () => {
  it("returns true if no token is provided", () => {
    expect(isTokenExpired(null)).toBe(true);
    expect(isTokenExpired("")).toBe(true);
  });

  it("returns true for a malformed or invalid JWT", () => {
    expect(isTokenExpired("not-a-real-jwt")).toBe(true);
    expect(isTokenExpired("header.payload")).toBe(true);
  });

  it("returns false if the token expiration is in the future", () => {
    const futureTime = Math.floor(Date.now() / 1000) + 3600;
    const mockPayload = btoa(JSON.stringify({ exp: futureTime }));
    const validToken = `header.${mockPayload}.signature`;

    expect(isTokenExpired(validToken)).toBe(false);
  });

  it("returns true if the token expiration is in the past", () => {
    const pastTime = Math.floor(Date.now() / 1000) - 3600;
    const mockPayload = btoa(JSON.stringify({ exp: pastTime }));
    const expiredToken = `header.${mockPayload}.signature`;

    expect(isTokenExpired(expiredToken)).toBe(true);
  });

  it("returns true if the token payload lacks an exp claim", () => {
    const mockPayload = btoa(JSON.stringify({ userId: "123" }));
    const badToken = `header.${mockPayload}.signature`;

    expect(isTokenExpired(badToken)).toBe(true);
  });
});
