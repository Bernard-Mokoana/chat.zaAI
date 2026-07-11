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
          <Loader2 className="mx-auto h-10 w-10 animate-spin" style={{ color: "#615676" }} />
          <p className="text-sm" style={{ color: "#5a4a6b" }}>
            Verifying your email address...
          </p>
        </div>
      )}

      {state.status === "success" && (
        <div className="space-y-4 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full" style={{ backgroundColor: "#7a6b8f" }}>
            <CheckCircle2 className="h-6 w-6" style={{ color: "#c7bcdc" }} />
          </div>
          <div>
            <h2 className="text-lg font-semibold" style={{ color: "#3d2f4d" }}>
              Email Verified
            </h2>
            <p className="mt-2 text-sm" style={{ color: "#5a4a6b" }}>
              Your account is confirmed. Redirecting to sign in...
            </p>
          </div>
        </div>
      )}

      {state.status === "error" && (
        <div className="space-y-4 text-center">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full" style={{ backgroundColor: "#7a6b8f" }}>
            <XCircle className="h-6 w-6" style={{ color: "#c7bcdc" }} />
          </div>
          <div>
            <h2 className="text-lg font-semibold" style={{ color: "#3d2f4d" }}>
              Verification Failed
            </h2>
            <p className="mt-2 text-sm" style={{ color: "#c44b6e" }}>
              {state.errorMessage}
            </p>
          </div>
          <Link
            href="/register"
            className="neu-btn inline-block px-6 py-2.5 text-sm font-medium"
            style={{ color: "#3d2f4d" }}
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
