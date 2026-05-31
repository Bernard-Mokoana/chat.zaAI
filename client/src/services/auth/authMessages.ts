import axios from "axios";
import type { ToastPayload } from "@/types/types";

type AuthAction = "login" | "register";

type ApiErrorPayload = {
  detail?: unknown;
};

function getDetail(error: unknown) {
  if (!axios.isAxiosError<ApiErrorPayload>(error)) return null;
  const detail = error.response?.data?.detail;
  return typeof detail === "string" ? detail : null;
}

export function getAuthErrorToast(action: AuthAction, error: unknown): ToastPayload | null {
  if (!axios.isAxiosError(error)) {
    return {
      title: action === "login" ? "Could not sign in" : "Could not create account",
      description: "Something went wrong. Please try again.",
      tone: "error",
    };
  }

  const status = error.response?.status;

  if (status === 429) {
    return null;
  }

  if (action === "login") {
    if (status === 401) {
      return {
        title: "Could not sign in",
        description: "Check your email and password, then try again.",
        tone: "error",
      };
    }

    return {
      title: "Could not sign in",
      description: getDetail(error) ?? "The sign-in request could not be completed.",
      tone: "error",
    };
  }

  if (status === 409) {
    return {
      title: "Email already registered",
      description: "Use the sign-in page or register with a different email address.",
      tone: "error",
    };
  }

  if (status === 400) {
    return {
      title: "Check your registration details",
      description: getDetail(error) ?? "Update the highlighted details and try again.",
      tone: "error",
    };
  }

  return {
    title: "Could not create account",
    description: getDetail(error) ?? "The registration request could not be completed.",
    tone: "error",
  };
}
