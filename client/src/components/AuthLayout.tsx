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
    <div className="flex min-h-screen items-center justify-center px-4 py-6" style={{ backgroundColor: "var(--bg)" }}>
      <div className="card w-full max-w-md p-8 sm:p-10">
        <h1 className="text-2xl font-bold tracking-tight text-center" style={{ color: "var(--text)" }}>
          {title}
        </h1>
        {subtitle && (
          <p className="mt-3 text-sm text-center mb-6" style={{ color: "var(--text-secondary)" }}>
            {subtitle}
          </p>
        )}

        {children}

        {footerLink && (
          <div className="mt-6 text-center">
            <Link
              href={footerLink.href}
              className="text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: "var(--accent)" }}
            >
              {footerLink.label}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
