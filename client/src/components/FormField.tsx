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
    <div className="space-y-2">
      <label
        htmlFor={fieldId}
        className="block text-sm font-semibold"
        style={{ color: "var(--text-secondary)" }}
      >
        {label}
      </label>
      <input
        id={fieldId}
        {...inputProps}
        className={`field w-full px-4 py-3 text-sm outline-none transition-all placeholder:opacity-60 disabled:opacity-60 disabled:cursor-not-allowed ${className || ""}`}
      />
      {error && (
        <p className="text-xs font-medium" style={{ color: "var(--danger)" }}>
          {error}
        </p>
      )}
    </div>
  );
}
