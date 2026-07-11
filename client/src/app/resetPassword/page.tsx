"use client";

import { Suspense, useState, useCallback, useRef, useEffect } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import type { FormEvent } from "react";
import axios from "axios";
import { resetPassword } from "@/services/auth/authApi";
import { showToast } from "@/services/toast/toastEvents";
import { validatePassword, getFieldError } from "@/utils/validation";
import AuthLayout from "@/components/AuthLayout";
import FormField from "@/components/FormField";
import AlertBanner from "@/components/AlertBanner";
import type { PasswordResetState } from "@/types/types";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [state, setState] = useState<PasswordResetState>({
    newPassword: "",
    confirmPassword: "",
    isPending: false,
    errorMessage: "",
    validationErrors: [],
  });

  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      if (state.isPending) return;

      if (!token) {
        setState((prev) => ({
          ...prev,
          errorMessage: "Reset token is missing. Please request a new reset link.",
        }));
        return;
      }

      const errors: Array<{ field: string; message: string }> = [];

      if (!state.newPassword) {
        errors.push({ field: "newPassword", message: "Password is required" });
      } else if (!validatePassword(state.newPassword)) {
        errors.push({
          field: "newPassword",
          message:
            "Password must contain at least 8 characters, including uppercase, lowercase, a number, and a special character (@$!%*?&)",
        });
      }

      if (state.newPassword !== state.confirmPassword) {
        errors.push({
          field: "confirmPassword",
          message: "Passwords do not match",
        });
      }

      if (errors.length > 0) {
        setState((prev) => ({
          ...prev,
          validationErrors: errors,
          errorMessage: "",
        }));
        return;
      }

      setState((prev) => ({ ...prev, isPending: true, validationErrors: [] }));

      try {
        await resetPassword({
          token: token!,
          new_password: state.newPassword,
        });

        showToast({
          title: "Password updated",
          description: "Your password has been changed. Redirecting to sign in...",
          tone: "success",
        });
        timeoutRef.current = setTimeout(() => router.push("/login"), 2000);

      } catch (err: unknown) {
        const detail =
          axios.isAxiosError(err) && typeof err.response?.data?.detail === "string"
            ? err.response.data.detail
            : "Something went wrong. Please try again.";

        setState((prev) => ({
          ...prev,
          errorMessage: detail as string,
        }));
      } finally {
        setState((prev) => ({ ...prev, isPending: false }));
      }
    },
    [state.newPassword, state.confirmPassword, state.isPending, token, router]
  );

  const clearErrors = useCallback(() => {
    setState((prev) => ({
      ...prev,
      validationErrors: [],
      errorMessage: "",
    }));
  }, []);

  return (
    <AuthLayout
      title="Set New Password"
      subtitle="Choose a new password for your account."
    >
      {state.errorMessage && (
        <div className="mb-4">
          <AlertBanner
            tone="error"
            message={state.errorMessage}
            onDismiss={() =>
              setState((prev) => ({ ...prev, errorMessage: "" }))
            }
          />
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="new-password"
          label="New Password"
          type="password"
          required
          disabled={state.isPending}
          value={state.newPassword}
          onChange={(e) => {
            setState((prev) => ({
              ...prev,
              newPassword: e.target.value,
            }));
            clearErrors();
          }}
          placeholder="Min 8 characters, uppercase, lowercase, number, special char"
          error={getFieldError(state.validationErrors, "newPassword")}
          autoComplete="new-password"
          autoFocus
        />

        <FormField
          id="confirm-password"
          label="Confirm Password"
          type="password"
          required
          disabled={state.isPending}
          value={state.confirmPassword}
          onChange={(e) => {
            setState((prev) => ({
              ...prev,
              confirmPassword: e.target.value,
            }));
            clearErrors();
          }}
          placeholder="Re-enter your password"
          error={getFieldError(state.validationErrors, "confirmPassword")}
          autoComplete="new-password"
        />

        <button
          type="submit"
          disabled={state.isPending}
          className="btn w-full py-3 text-sm font-semibold"
          style={{ color: "var(--accent-text)" }}
        >
          {state.isPending ? "Updating..." : "Update Password"}
        </button>
      </form>
    </AuthLayout>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ResetPasswordForm />
    </Suspense>
  );
}
