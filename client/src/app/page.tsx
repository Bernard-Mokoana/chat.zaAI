"use client";

import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-linear-to-br from-slate-100 via-white to-blue-50 px-4 py-6 sm:py-12">
      <section className="w-full max-w-2xl rounded-xl border border-slate-200 bg-white p-8 shadow-lg sm:p-12 dark:border-slate-800 dark:bg-slate-950">
        {/* Header */}
        <div className="mb-8 sm:mb-10">
          <p className="mb-2 text-xs font-bold uppercase tracking-widest text-slate-500 dark:text-slate-400">
            AI Chatbot
          </p>
          <h1 className="text-3xl sm:text-4xl font-bold tracking-tight text-slate-900 dark:text-slate-50">
            Welcome to 3DoT
          </h1>
          <p className="mt-4 text-base sm:text-lg text-slate-600 dark:text-slate-300">
            Sign in to continue chatting, or create a new account.
          </p>
        </div>

        {/* Button Group */}
        <div className="flex flex-col gap-3 sm:flex-row sm:gap-4">
          <Link
            href="/login"
            className="flex-1 rounded-lg bg-linear-to-r from-slate-900 to-slate-800 px-6 py-3.5 text-center font-semibold text-white shadow-md transition-all hover:shadow-lg hover:from-slate-800 hover:to-slate-700 dark:from-slate-700 dark:to-slate-800"
          >
            Sign In
          </Link>
          <Link
            href="/register"
            className="flex-1 rounded-lg border-2 border-slate-200 bg-white px-6 py-3.5 text-center font-semibold text-slate-900 transition-all hover:bg-slate-50 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50 dark:hover:bg-slate-800"
          >
            Create Account
          </Link>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs sm:text-sm text-slate-500 dark:text-slate-400">
          Your secure AI chatbot platform
        </p>
      </section>
    </main>
  );
}
