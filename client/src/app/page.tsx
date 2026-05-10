"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "2rem",
        fontFamily: "ui-sans-serif, system-ui, -apple-system, Segoe UI",
        background:
          "radial-gradient(circle at 20% 20%, #f5f7ff 0%, #ffffff 45%, #f7fbff 100%)",
        color: "#0f172a",
      }}
    >
      <section
        style={{
          width: "100%",
          maxWidth: "620px",
          borderRadius: "16px",
          padding: "2.5rem",
          background: "#ffffff",
          boxShadow:
            "0 30px 70px rgba(15, 23, 42, 0.12), 0 6px 18px rgba(15, 23, 42, 0.08)",
          border: "1px solid #e2e8f0",
        }}
      >
        <div style={{ marginBottom: "1.5rem" }}>
          <p
            style={{
              fontSize: "0.85rem",
              fontWeight: 700,
              letterSpacing: "0.2em",
              textTransform: "uppercase",
              color: "#64748b",
              marginBottom: "0.5rem",
            }}
          >
            AI Chatbot
          </p>
          <h1 style={{ fontSize: "2rem", margin: 0 }}>
            Welcome to FullStack AI Chatbot
          </h1>
          <p style={{ color: "#475569", marginTop: "0.75rem" }}>
            Sign in to continue chatting, or create a new account.
          </p>
        </div>

        <div style={{ display: "grid", gap: "0.75rem" }}>
          <Link
            href="/login"
            style={{
              display: "inline-block",
              textAlign: "center",
              textDecoration: "none",
              padding: "0.85rem 1.25rem",
              borderRadius: "10px",
              background: "linear-gradient(135deg, #0f172a, #1e293b)",
              color: "#ffffff",
              fontWeight: 700,
              border: "none",
            }}
          >
            Sign In
          </Link>
          <Link
            href="/register"
            style={{
              display: "inline-block",
              textAlign: "center",
              textDecoration: "none",
              padding: "0.85rem 1.25rem",
              borderRadius: "10px",
              background: "#ffffff",
              color: "#0f172a",
              fontWeight: 700,
              border: "1px solid #cbd5e1",
            }}
          >
            Create Account
          </Link>
        </div>
      </section>
    </main>
  );
}
