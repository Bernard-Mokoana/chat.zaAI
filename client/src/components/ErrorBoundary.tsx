"use client";

import { Component } from "react";
import { AlertTriangle } from "lucide-react";
import type { ErrorBoundaryProps, ErrorBoundaryState } from "@/types/types";

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("Error caught by boundary:", error, errorInfo);
  }

  resetError = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError && this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error);
      }

      return (
        <div className="flex min-h-screen items-center justify-center px-4" style={{ backgroundColor: "#9489a9" }}>
          <div className="neu-flat w-full max-w-md p-6">
            <div className="flex gap-3">
              <AlertTriangle className="h-5 w-5 shrink-0" style={{ color: "#c44b6e" }} />
              <div>
                <h3 className="font-semibold" style={{ color: "#3d2f4d" }}>
                  Something went wrong
                </h3>
                <p className="mt-1 text-sm" style={{ color: "#5a4a6b" }}>
                  {this.state.error.message ||
                    "An unexpected error occurred. Please try reloading the page."}
                </p>
                <button
                  onClick={this.resetError}
                  className="neu-btn mt-4 px-4 py-2 text-sm font-medium"
                  style={{ color: "#3d2f4d" }}
                >
                  Try Again
                </button>
              </div>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
