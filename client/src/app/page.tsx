"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center px-4 py-6 sm:py-12" style={{ backgroundColor: "#9489a9" }}>
      <section className="neu-flat w-full max-w-2xl p-8 sm:p-12">
        <div className="mb-8 sm:mb-10">
          <p className="mb-2 text-xs font-bold uppercase tracking-widest" style={{ color: "#5a4a6b" }}>
            AI Chatbot
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight" style={{ color: "#3d2f4d" }}>
            Welcome to 3DoT
          </h1>
          <p className="mt-4 text-base sm:text-lg" style={{ color: "#5a4a6b" }}>
            Sign in to continue chatting, or create a new account.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
          <Link
            href="/login"
            className="neu-btn flex-1 px-6 py-3.5 text-center font-semibold"
            style={{ color: "#3d2f4d" }}
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="neu-btn flex-1 px-6 py-3.5 text-center font-semibold"
            style={{ color: "#3d2f4d" }}
          >
            Create Account
          </Link>
        </div>

        <p className="mt-8 text-center text-xs sm:text-sm" style={{ color: "#5a4a6b" }}>
          Your secure AI chatbot platform
        </p>
      </section>
    </main>
  );
}
