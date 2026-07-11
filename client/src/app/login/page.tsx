"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { login } from "@/services/auth/authApi";
import { getAuthErrorToast } from "@/services/auth/authMessages";
import { setAccessToken, setAuthUser } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import { validateLoginForm, getFieldError } from "@/utils/validation";
import AuthLayout from "@/components/AuthLayout";
import FormField from "@/components/FormField";
import Link from "next/link";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<
    Array<{ field: string; message: string }>
  >([]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      if (isSubmitting) return;
      setIsSubmitting(true);

      const validation = validateLoginForm(email, password);
      if (!validation.isValid) {
        setValidationErrors(validation.errors);
        setIsSubmitting(false);
        return;
      }

      setValidationErrors([]);

      try {
        const auth = await login({
          email: email.trim().toLowerCase(),
          password,
        });
        setAccessToken(auth.access_token);
        setAuthUser(auth.user);
        showToast({
          title: "Signed in",
          description: `Welcome back, ${auth.user.name}.`,
          tone: "success",
        });
        router.push("/chat");
      } catch (error: unknown) {
        const toast = getAuthErrorToast("login", error);
        if (toast) showToast(toast);
      } finally {
        setIsSubmitting(false);
      }
    },
    [email, password, isSubmitting, router]
  );

  return (
    <AuthLayout
      title="Sign In"
      subtitle="Welcome back. Continue to your chat."
      footerLink={{ href: "/register", label: "Create an account" }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="login-email"
          label="Email Address"
          type="email"
          required
          disabled={isSubmitting}
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);

            if (validationErrors.length > 0) {
              setValidationErrors([]);
            }
          }}
          placeholder="Enter your email"
          error={getFieldError(validationErrors, "email")}
          autoComplete="email"
          autoFocus
        />

        <FormField
          id="login-password"
          label="Password"
          type="password"
          required
          disabled={isSubmitting}
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            if (validationErrors.length > 0) {
              setValidationErrors([]);
            }
          }}
          placeholder="Enter your password"
          error={getFieldError(validationErrors, "password")}
          autoComplete="current-password"
        />

        <button
          type="submit"
          disabled={isSubmitting}
          className="btn w-full py-3 text-sm font-semibold"
          style={{ color: "var(--accent-text)" }}
        >
          {isSubmitting ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <Link
          href="/forgotPassword"
          className="text-sm font-medium transition-colors hover:opacity-80"
          style={{ color: "var(--accent)" }}
        >
          Forgot your password?
        </Link>
      </div>
    </AuthLayout>
  );
}
