"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";
import type { FormEvent } from "react";
import { forgotPassword } from "@/services/auth/authApi";
import { showToast } from "@/services/toast/toastEvents";
import { validateForgotPasswordForm, getFieldError } from "@/utils/validation";
import AuthLayout from "@/components/AuthLayout";
import FormField from "@/components/FormField";
import AlertBanner from "@/components/AlertBanner";

export default function ForgotPasswordPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [isPending, setIsPending] = useState(false);
  const [validationErrors, setValidationErrors] = useState<
    Array<{ field: string; message: string }>
  >([]);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      if (isPending) return;

      const validation = validateForgotPasswordForm(email);
      if (!validation.isValid) {
        setValidationErrors(validation.errors);
        return;
      }

      setValidationErrors([]);
      setErrorMessage("");
      setSuccessMessage("");
      setIsPending(true);

      try {
        const response = await forgotPassword({ email: email.trim().toLowerCase() });
        showToast({
          title: "Recovery email sent",
          description: response.message,
          tone: "success",
        });
        setSuccessMessage(response.message);
        setEmail("");
      } catch (err: unknown) {
        const detail =
          axios.isAxiosError(err) && typeof err.response?.data?.detail === "string"
            ? err.response.data.detail
            : "Something went wrong. Please try again.";
        setErrorMessage(detail);
      } finally {
        setIsPending(false);
      }
    },
    [email, isPending]
  );

  return (
    <AuthLayout
      title="Reset Password"
      subtitle="Enter your email address and we'll send you a reset link."
      footerLink={{ href: "/login", label: "Back to Sign In" }}
    >
      {errorMessage && (
        <div className="mb-4">
          <AlertBanner
            tone="error"
            message={errorMessage}
            onDismiss={() => setErrorMessage("")}
          />
        </div>
      )}

      {successMessage && (
        <div className="mb-4">
          <AlertBanner
            tone="success"
            message={successMessage}
            onDismiss={() => setSuccessMessage("")}
          />
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="recovery-email"
          label="Email Address"
          type="email"
          required
          disabled={isPending}
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (validationErrors.length > 0) {
              setValidationErrors([]);
            }
          }}
          placeholder="you@example.com"
          error={getFieldError(validationErrors, "email")}
          autoComplete="email"
          autoFocus
        />

        <button
          type="submit"
          disabled={isPending}
          className="neu-btn w-full py-3 text-sm font-semibold"
          style={{ color: "#3d2f4d" }}
        >
          {isPending ? "Sending..." : "Send Reset Link"}
        </button>
      </form>
    </AuthLayout>
  );
}
