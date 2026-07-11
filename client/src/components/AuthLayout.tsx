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
    <div className="flex min-h-screen items-center justify-center px-4 py-6" style={{ backgroundColor: "#9489a9" }}>
      <div className="neu-flat w-full max-w-md p-8 sm:p-10">
        <h1 className="text-2xl font-bold tracking-tight text-center" style={{ color: "#3d2f4d" }}>
          {title}
        </h1>
        {subtitle && (
          <p className="mt-3 text-sm text-center mb-6" style={{ color: "#5a4a6b" }}>
            {subtitle}
          </p>
        )}

        {children}

        {footerLink && (
          <div className="mt-6 text-center">
            <Link
              href={footerLink.href}
              className="text-sm font-medium transition-colors hover:opacity-80"
              style={{ color: "#615676" }}
            >
              {footerLink.label}
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
