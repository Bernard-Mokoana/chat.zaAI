"use client";

import { useState, FormEvent } from "react";
import Link from "next/link";
import { forgotPassword } from "@/services/auth/authApi";

export default function ForgotPasswordPage() {
  const [emailValue, setEmailValue] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [statusFeedback, setStatusFeedback] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const handlePasswordResetDispatch = async (event: FormEvent) => {
    event.preventDefault();
    setIsPending(true);
    setErrorMessage("");
    setStatusFeedback("");

    try {
      const serverResponse = await forgotPassword({ email: emailValue });
      setStatusFeedback(serverResponse.message);
    } catch (err: any) {
      setErrorMessage(err.response?.data?.detail || "An internal client routing error occurred.");
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50 text-center">Recover Password</h1>
        <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 text-center mb-6">
          Enter your email address to receive a password reset link
        </p>

        {statusFeedback ? (
          <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/30 dark:bg-emerald-950/20 dark:text-emerald-400 text-center">
            {statusFeedback}
          </div>
        ) : (
          <form onSubmit={handlePasswordResetDispatch} className="space-y-4">
            {errorMessage && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/30 dark:bg-rose-950/20 dark:text-rose-400">
                {errorMessage}
              </div>
            )}
            
            <div>
              <label htmlFor="recovery-email" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Account Email
              </label>
              <input
                id="recovery-email"
                type="email"
                required
                disabled={isPending}
                value={emailValue}
                onChange={(e) => setEmailValue(e.target.value)}
                placeholder="developer@domain.local"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-all focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50 disabled:opacity-60"
              />
            </div>

            <button
              type="submit"
              disabled={isPending}
              className="w-full rounded-lg bg-blue-600 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "Validating Account..." : "Dispatch Link Parameters"}
            </button>
          </form>
        )}

        <div className="mt-6 text-center">
          <Link href="/login" className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400">
            Return to Identity Validation
          </Link>
        </div>
      </div>
    </div>
  );
}