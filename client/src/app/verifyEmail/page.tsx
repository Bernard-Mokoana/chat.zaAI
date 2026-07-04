"use client";

import { Suspense, useEffect, useState, useRef } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { verifyEmail } from "@/services/auth/authApi";
import AuthLayout from "@/components/AuthLayout";
import type { VerificationState } from "@/types/types";

function VerifyEmailForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const hasToken = Boolean(token);
  const [state, setState] = useState<VerificationState>({
    status: hasToken ? "verifying" : "error",
    errorMessage: hasToken
      ? ""
      : "No verification token found in the URL. Please check your email link and try again.",
  });

  const effectRan = useRef(false);

  useEffect(() => {
    if (effectRan.current) return;

    if (!token) {
      router.replace("/register");
      return;
    }

    let mounted = true;
    let timeoutId: ReturnType<typeof setTimeout> | undefined;

    const executeVerification = async () => {
      try {
        await verifyEmail(token);
        if (mounted) setState({ status: "success", errorMessage: "" });

        timeoutId = setTimeout(() => {
          if (mounted) router.push("/login");
        }, 3500);
      } catch {
        if (mounted) {
          setState({
          status: "error",
          errorMessage:
            "Verification failed. The link may have expired. Please request a new one.",
        });
       }
      }
    };

    executeVerification();
    effectRan.current = true;

    return () => {
      mounted = false;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [router, token]);

  return (
    <AuthLayout title="Email Verification">
      {state.status === "verifying" && (
        <div className="space-y-4 text-center">
          <Loader2 className="mx-auto h-10 w-10 animate-spin text-blue-600" />
          <p className="text-sm text-slate-600 dark:text-slate-400">
            Verifying your email address...
          </p>
        </div>
      )}

      {state.status === "success" && (
        <div className="space-y-4 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 dark:bg-emerald-950/50">
            <CheckCircle2 className="h-6 w-6 text-emerald-600 dark:text-emerald-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
              Email Verified
            </h2>
            <p className="mt-2 text-sm text-slate-600 dark:text-slate-400">
              Your account is confirmed. Redirecting to sign in...
            </p>
          </div>
        </div>
      )}

      {state.status === "error" && (
        <div className="space-y-4 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 dark:bg-rose-950/50">
            <XCircle className="h-6 w-6 text-rose-600 dark:text-rose-400" />
          </div>
          <div>
            <h2 className="text-lg font-semibold text-slate-900 dark:text-slate-50">
              Verification Failed
            </h2>
            <p className="mt-2 text-sm text-rose-600 dark:text-rose-400">
              {state.errorMessage}
            </p>
          </div>
          <Link
            href="/register"
            className="inline-block rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-medium text-white transition-colors hover:bg-blue-700"
          >
            Back to Registration
          </Link>
        </div>
      )}
    </AuthLayout>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <VerifyEmailForm />
    </Suspense>
  );
}
