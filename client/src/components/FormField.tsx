"use client";

import type { FormFieldProps } from "@/types/types";

export default function FormField({
  label,
  id,
  error,
  className,
  ...inputProps
}: FormFieldProps) {
  const fieldId = id ?? (inputProps.name as string | undefined);

  return (
    <div className="space-y-1.5">
      <label
        htmlFor={fieldId}
        className="block text-sm font-medium text-slate-700 dark:text-slate-300"
      >
        {label}
      </label>
      <input
        id={fieldId}
        {...inputProps}
        className={`w-full rounded-lg border bg-white px-4 py-2.5 text-sm text-slate-900 outline-none transition-all focus:ring-2 dark:bg-slate-900 dark:text-slate-50 ${
          error
            ? "border-rose-500 focus:border-rose-500 focus:ring-rose-500"
            : "border-slate-300 focus:border-blue-500 focus:ring-blue-500 dark:border-slate-700"
        } disabled:opacity-60 disabled:cursor-not-allowed ${className || ""}`}
      />
      {error && (
        <p className="text-xs font-medium text-red-500 dark:text-red-400">
          {error}
        </p>
      )}
    </div>
  );
}