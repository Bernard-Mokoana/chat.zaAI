"use client";

import { useEffect, useState, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { verifyEmail } from "@/services/auth/authApi";

export default function VerifyEmailPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"verifying" | "success" | "error">("verifying");
  const [errorDetails, setErrorDetails] = useState("");
  const effectRan = useRef(false);

  useEffect(() => {
    // Standard React 18 / NextJS mount protection for write-once API interactions
    if (effectRan.current) return;

    if (!token) {
      setStatus("error");
      setErrorDetails("A validation token was not found in the URL parameter list.");
      return;
    }

    const executeVerification = async () => {
      try {
        await verifyEmail(token);
        setStatus("success");
        setTimeout(() => {
          router.push("/login");
        }, 3500);
      } catch (err: any) {
        setStatus("error");
        setErrorDetails(err.response?.data?.detail || "Verification failed. The token may be structurally invalid or expired.");
      }
    };

    executeVerification();
    return () => {
      effectRan.current = true;
    };
  }, [token, router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 text-center shadow-sm dark:border-slate-800 dark:bg-slate-950">
        {status === "verifying" && (
          <div className="space-y-4">
            <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
            <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-50">Confirming Email Address</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Communicating secure parameters to our server cluster...</p>
          </div>
        )}

        {status === "success" && (
          <div className="space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 dark:bg-emerald-950/50 dark:text-emerald-400">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">Account Confirmed!</h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">Verification complete. Transferring you to authentication panel...</p>
          </div>
        )}

        {status === "error" && (
          <div className="space-y-4">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-950/50 dark:text-rose-400">
              <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-xl font-bold text-slate-900 dark:text-slate-50">Verification Timed Out</h1>
            <p className="text-sm text-rose-600 dark:text-rose-400">{errorDetails}</p>
            <div className="pt-2">
              <Link href="/register" className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400">
                Return to Registration
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}