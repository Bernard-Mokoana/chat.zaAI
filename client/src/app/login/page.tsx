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

      const validation = validateLoginForm(email, password);
      if (!validation.isValid) {
        setValidationErrors(validation.errors);
        return;
      }

      setValidationErrors([]);
      if (isSubmitting) return;
      setIsSubmitting(true);

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
          placeholder="you@example.com"
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
          className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Signing in..." : "Sign In"}
        </button>
      </form>

      <div className="mt-6 text-center">
        <a
          href="/forgotPassword"
          className="text-sm font-medium text-blue-600 transition-colors hover:text-blue-700 dark:text-blue-400 dark:hover:text-blue-300"
        >
          Forgot your password?
        </a>
      </div>
    </AuthLayout>
  );
}
