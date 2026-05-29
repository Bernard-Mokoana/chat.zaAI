"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import { login } from "@/services/auth/authApi";
import { setAccessToken, setAuthUser } from "@/services/storage/chatStorage";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedEmail = email.trim().toLowerCase();

    if (!trimmedEmail || !password) {
      setError("Please fill in all fields");
      return;
    };
    if (isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const auth = await login({ email: trimmedEmail, password });
      setAccessToken(auth.access_token);
      setAuthUser(auth.user);

      router.push("/chat");
    } catch (error: unknown) {
      const message = axios.isAxiosError(error)
        ? error.response?.data?.detail || error.message
        : error instanceof Error
          ? error.message
          : "Login failed.";
      setError(typeof message === "string" ? message : "Login failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "1.5rem", background: "linear-gradient(180deg, #f8fafc 0%, #eef2ff 100%)" }}>
      <section style={{ width: "100%", maxWidth: 520, background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16, padding: "2rem", boxShadow: "0 12px 32px rgba(15, 23, 42, 0.08)" }}>
        <h1 style={{ margin: 0, fontSize: "1.8rem", color: "#0f172a" }}>Sign In</h1>
        <p style={{ color: "#475569", marginTop: "0.5rem" }}>Welcome back. Continue to your chat.</p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.9rem", marginTop: "1rem" }}>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={{ padding: "0.75rem", borderRadius: 10, border: "1px solid #cbd5e1" }} />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password" style={{ padding: "0.75rem", borderRadius: 10, border: "1px solid #cbd5e1" }} />

          {error ? <p style={{ margin: 0, color: "#b91c1c", fontSize: "0.9rem" }}>{error}</p> : null}

          <button type="submit" disabled={isSubmitting} style={{ padding: "0.8rem", borderRadius: 10, border: "none", background: "#1d4ed8", color: "#fff", fontWeight: 600, cursor: "pointer", opacity: isSubmitting ? 0.75 : 1 }}>
            {isSubmitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <p style={{ marginTop: "1rem", color: "#334155" }}>
          New here? <Link href="/register">Create an account</Link>
        </p>
      </section>
    </main>
  );
}
