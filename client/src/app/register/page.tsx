"use client";

import { useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { register } from "@/services/auth/authApi";
import { getAuthErrorToast } from "@/services/auth/authMessages";
import { setAccessToken, setAuthUser } from "@/services/storage/chatStorage";
import { showToast } from "@/services/toast/toastEvents";
import { validateRegisterForm, getFieldError } from "@/utils/validation";
import AuthLayout from "@/components/AuthLayout";
import FormField from "@/components/FormField";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [validationErrors, setValidationErrors] = useState<
    Array<{ field: string; message: string }>
  >([]);

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();

      const validation = validateRegisterForm(
        name,
        email,
        password,
        confirmPassword
      );
      if (!validation.isValid) {
        setValidationErrors(validation.errors);
        return;
      }

      setValidationErrors([]);
      if (isSubmitting) return;
      setIsSubmitting(true);

      try {
        const auth = await register({
          name: name.trim(),
          email: email.trim().toLowerCase(),
          password,
        });
        setAccessToken(auth.access_token);
        setAuthUser(auth.user);
        showToast({
          title: "Account created",
          description: `${auth.user.name}, check your email to verify your account so that you can access the chat.`,
          tone: "success",
        });
      } catch (error: unknown) {
        const toast = getAuthErrorToast("register", error);
        if (toast) showToast(toast);
      } finally {
        setIsSubmitting(false);
      }
    },
    [name, email, password, confirmPassword, isSubmitting, router]
  );

  const clearErrors = useCallback(() => {
    if (validationErrors.length > 0) {
      setValidationErrors([]);
    }
  }, [validationErrors.length]);

  return (
    <AuthLayout
      title="Create Account"
      subtitle="Register and start chatting."
      footerLink={{ href: "/login", label: "Already have an account? Sign in" }}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        <FormField
          id="register-name"
          label="Full Name"
          type="text"
          required
          disabled={isSubmitting}
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            clearErrors();
          }}
          placeholder="John Doe"
          error={getFieldError(validationErrors, "name")}
          autoComplete="name"
          autoFocus
        />

        <FormField
          id="register-email"
          label="Email Address"
          type="email"
          required
          disabled={isSubmitting}
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            clearErrors();
          }}
          placeholder="you@example.com"
          error={getFieldError(validationErrors, "email")}
          autoComplete="email"
        />

        <FormField
          id="register-password"
          label="Password"
          type="password"
          required
          disabled={isSubmitting}
          value={password}
          onChange={(e) => {
            setPassword(e.target.value);
            clearErrors();
          }}
          placeholder="Min 8 characters, uppercase, lowercase, number, special char"
          error={getFieldError(validationErrors, "password")}
          autoComplete="new-password"
        />

        <FormField
          id="register-confirm-password"
          label="Confirm Password"
          type="password"
          required
          disabled={isSubmitting}
          value={confirmPassword}
          onChange={(e) => {
            setConfirmPassword(e.target.value);
            clearErrors();
          }}
          placeholder="Re-enter your password"
          error={getFieldError(validationErrors, "confirmPassword")}
          autoComplete="new-password"
        />

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full rounded-lg bg-blue-600 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-blue-700 disabled:bg-slate-300 disabled:cursor-not-allowed"
        >
          {isSubmitting ? "Creating account..." : "Register"}
        </button>
      </form>
    </AuthLayout>
  );
}
