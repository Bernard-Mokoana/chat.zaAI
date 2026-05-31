import type { ToastPayload } from "@/types/types";

const TOAST_EVENT = "app:toast";

export function showToast(payload: ToastPayload) {
  if (typeof window === "undefined") return;
  window.dispatchEvent(
    new CustomEvent<ToastPayload>(TOAST_EVENT, { detail: payload }),
  );
}

export function onToast(handler: (payload: ToastPayload) => void) {
  if (typeof window === "undefined") return () => {};

  const listener = (event: Event) => {
    handler((event as CustomEvent<ToastPayload>).detail);
  };

  window.addEventListener(TOAST_EVENT, listener);
  return () => window.removeEventListener(TOAST_EVENT, listener);
}
