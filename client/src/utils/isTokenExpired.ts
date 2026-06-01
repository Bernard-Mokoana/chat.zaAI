// Use a clock-skew buffer so a token that expires in 30 sec is treated as already expired before the next API call fails
// (prevents the race condition where the token looks valid locally but fails the API call).
export function isTokenExpired(token: string, clockSkewSeconds = 30): boolean {
  if (!token) return true;

  const parts = token.split(".");
  if (parts.length != 3) return true;

  try {
    // Base64Url -> Base64 -> JSON
    const base64 = parts[1].replace(/-/g, "+").replace(/_/g, "/");
    const padded = base64.padEnd(
      base64.length + ((4 - (base64.length % 4)) % 4),
      "=",
    );
    const payload = JSON.parse(atob(padded));

    if (typeof payload.exp !== "number") {
      return true;
    }

    const nowSeconds = Math.floor(Date.now() / 1000);
    return payload.exp < nowSeconds + clockSkewSeconds;
  } catch {
    return true;
  }
}
