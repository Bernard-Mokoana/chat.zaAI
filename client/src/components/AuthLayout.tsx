"use client";

import Link from "next/link";
import type { AuthLayoutProps } from "@/types/types";

export default function AuthLayout({
  title,
  subtitle,
  children,
  footerLink,
}: AuthLayoutProps) {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4 dark:bg-slate-900">
      <div className="w-full max-w-md rounded-xl border border-slate-200 bg-white p-8 shadow-sm dark:border-slate-800 dark:bg-slate-950">
        <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-slate-50 text-center">
          {title}
        </h1>
        {subtitle && (
          <p className="mt-2 text-sm text-slate-500 dark:text-slate-400 text-center mb-6">
            {subtitle}
          </p>
        )}

        {children}

        {footerLink && (
          <div className="mt-6 text-center">
            <Link
              href={footerLink.href}
              className="text-sm font-medium text-blue-600 hover:underline dark:text-blue-400"
            >
              {footerLink.label}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
