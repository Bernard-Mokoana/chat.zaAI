"use client";

import { useState, FormEvent } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { resetPassword } from "@/services/auth/authApi";

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const verificationToken = searchParams.get("token");

  const [passwordValue, setPasswordValue] = useState("");
  const [passwordConfirm, setPasswordConfirm] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [localValidationMessage, setLocalValidationMessage] = useState("");
  const [completionState, setCompletionState] = useState(false);

  const handlePasswordMutationSubmit = async (event: FormEvent) => {
    event.preventDefault();
    setLocalValidationMessage("");

    if (!verificationToken) {
      setLocalValidationMessage("Unable to execute transaction. Password mutation security token missing from query stream.");
      return;
    }

    if (passwordValue.length < 8) {
      setLocalValidationMessage("Password parameter failed length validation checks (minimum required configuration threshold is 8 entries).");
      return;
    }

    if (passwordValue !== passwordConfirm) {
      setLocalValidationMessage("Parameter validation divergence noted: Target password strings do not match.");
      return;
    }

    setIsPending(true);

    try {
      await resetPassword({
        token: verificationToken,
        new_password: passwordValue,
      });
      setCompletionState(true);
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err: any) {
      setLocalValidationMessage(err.response?.data?.detail || "Failed to commit record mutation. Token has expired or was previously consumed.");
    } finally {
      setIsPending(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50 text-center mb-6">Update Profile Passwords</h1>

        {completionState ? (
          <div className="space-y-4 text-center">
            <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-4 text-sm text-emerald-800 dark:border-emerald-900/30 dark:bg-emerald-950/20 dark:text-emerald-400">
              Identity parameters mutation successfully written to disk. Redirecting...
            </div>
            <Link href="/login" className="inline-block text-sm font-medium text-blue-600 hover:underline dark:text-blue-400">
              Click here to manually override redirection wait times
            </Link>
          </div>
        ) : (
          <form onSubmit={handlePasswordMutationSubmit} className="space-y-4">
            {localValidationMessage && (
              <div className="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 dark:border-rose-900/30 dark:bg-rose-950/20 dark:text-rose-400">
                {localValidationMessage}
              </div>
            )}
            
            <div>
              <label htmlFor="new-secret" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                New Target Password
              </label>
              <input
                id="new-secret"
                type="password"
                required
                disabled={isPending || !verificationToken}
                value={passwordValue}
                onChange={(e) => setPasswordValue(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-all focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50 disabled:opacity-60"
              />
            </div>

            <div>
              <label htmlFor="confirm-secret" className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-1">
                Confirm Selected Password
              </label>
              <input
                id="confirm-secret"
                type="password"
                required
                disabled={isPending || !verificationToken}
                value={passwordConfirm}
                onChange={(e) => setPasswordConfirm(e.target.value)}
                placeholder="••••••••"
                className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 outline-none transition-all focus:border-blue-500 focus:ring-1 focus:ring-blue-500 dark:border-slate-700 dark:bg-slate-900 dark:text-slate-50 disabled:opacity-60"
              />
            </div>

            <button
              type="submit"
              disabled={isPending || !verificationToken}
              className="w-full rounded-lg bg-blue-600 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:opacity-50"
            >
              {isPending ? "Updating Database Context..." : "Commit Secure Mutation"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}