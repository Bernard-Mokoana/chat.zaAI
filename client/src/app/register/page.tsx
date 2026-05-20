"use client";

import Link from "next/link";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { register } from "@/services/auth/authApi";
import { setAccessToken, setChatName } from "@/services/storage/chatStorage";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedName = name.trim();
    const trimmedEmail = email.trim().toLowerCase();

    if (password.length < 8) {
      setError("Password must be at least 8 characters long");
      return;
    }

    if (!trimmedName || !trimmedEmail || !password || isSubmitting) return;

    setIsSubmitting(true);
    setError(null);

    try {
      const auth = await register({ name: trimmedName, email: trimmedEmail, password });
      setAccessToken(auth.access_token);
      setChatName(trimmedName);

      router.push("/chat");
    } catch (e: any) {
      const message = e?.response?.data?.detail || e?.message || "Registration failed.";
      setError(typeof message === "string" ? message : "Registration failed.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: "1.5rem", background: "linear-gradient(180deg, #f8fafc 0%, #ecfeff 100%)" }}>
      <section style={{ width: "100%", maxWidth: 520, background: "#fff", border: "1px solid #e2e8f0", borderRadius: 16, padding: "2rem", boxShadow: "0 12px 32px rgba(15, 23, 42, 0.08)" }}>
        <h1 style={{ margin: 0, fontSize: "1.8rem", color: "#0f172a" }}>Create Account</h1>
        <p style={{ color: "#475569", marginTop: "0.5rem" }}>Register and start chatting.</p>

        <form onSubmit={handleSubmit} style={{ display: "grid", gap: "0.9rem", marginTop: "1rem" }}>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Name" style={{ padding: "0.75rem", borderRadius: 10, border: "1px solid #cbd5e1" }} />
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" style={{ padding: "0.75rem", borderRadius: 10, border: "1px solid #cbd5e1" }} />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password (min 8 chars)" style={{ padding: "0.75rem", borderRadius: 10, border: "1px solid #cbd5e1" }} />

          {error ? <p style={{ margin: 0, color: "#b91c1c", fontSize: "0.9rem" }}>{error}</p> : null}

          <button type="submit" disabled={isSubmitting} style={{ padding: "0.8rem", borderRadius: 10, border: "none", background: "#0f766e", color: "#fff", fontWeight: 600, cursor: "pointer", opacity: isSubmitting ? 0.75 : 1 }}>
            {isSubmitting ? "Creating account..." : "Register"}
          </button>
        </form>

        <p style={{ marginTop: "1rem", color: "#334155" }}>
          Already have an account? <Link href="/login">Sign in</Link>
        </p>
      </section>
    </main>
  );
}

