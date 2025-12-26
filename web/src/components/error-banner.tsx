"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertCircle, Clock, X, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface RateLimitInfo {
  limit_type: string;
  limit_type_friendly: string;
  retry_after: number | null;
  retry_after_friendly: string;
  suggestion: string;
}

export interface ErrorInfo {
  message: string;
  error_type: "rate_limit" | "general";
  rate_limit?: RateLimitInfo;
}

interface ErrorBannerProps {
  error: ErrorInfo | null;
  onDismiss: () => void;
}

const limitTypeIcons: Record<string, string> = {
  TPM: "Tokens/min",
  RPM: "Requests/min",
  RPD: "Requests/day",
  TPD: "Tokens/day",
  unknown: "Rate limit",
};

export function ErrorBanner({ error, onDismiss }: ErrorBannerProps) {
  if (!error) return null;

  const isRateLimit = error.error_type === "rate_limit" && error.rate_limit;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -20 }}
        transition={{ duration: 0.3 }}
        className="mb-6"
      >
        <div
          className={`rounded-lg border p-4 ${
            isRateLimit
              ? "bg-amber-50 border-amber-200 dark:bg-amber-950/20 dark:border-amber-800"
              : "bg-red-50 border-red-200 dark:bg-red-950/20 dark:border-red-800"
          }`}
        >
          <div className="flex items-start gap-3">
            <div
              className={`flex h-10 w-10 shrink-0 items-center justify-center rounded-full ${
                isRateLimit
                  ? "bg-amber-100 dark:bg-amber-900/40"
                  : "bg-red-100 dark:bg-red-900/40"
              }`}
            >
              {isRateLimit ? (
                <Zap className="h-5 w-5 text-amber-600 dark:text-amber-400" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <h3
                className={`font-semibold ${
                  isRateLimit
                    ? "text-amber-800 dark:text-amber-200"
                    : "text-red-800 dark:text-red-200"
                }`}
              >
                {isRateLimit ? "Groq Rate Limit Reached" : "Error Occurred"}
              </h3>

              {isRateLimit && error.rate_limit ? (
                <div className="mt-2 space-y-2">
                  <div className="flex flex-wrap gap-3 text-sm">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium ${
                        isRateLimit
                          ? "bg-amber-200/60 text-amber-800 dark:bg-amber-800/40 dark:text-amber-200"
                          : ""
                      }`}
                    >
                      <Zap className="h-3.5 w-3.5" />
                      {limitTypeIcons[error.rate_limit.limit_type] ||
                        error.rate_limit.limit_type_friendly}
                    </span>

                    {error.rate_limit.retry_after && (
                      <span
                        className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full font-medium ${
                          isRateLimit
                            ? "bg-amber-200/60 text-amber-800 dark:bg-amber-800/40 dark:text-amber-200"
                            : ""
                        }`}
                      >
                        <Clock className="h-3.5 w-3.5" />
                        Retry in {error.rate_limit.retry_after_friendly}
                      </span>
                    )}
                  </div>

                  <p className="text-sm text-amber-700 dark:text-amber-300">
                    {error.rate_limit.suggestion}
                  </p>
                </div>
              ) : (
                <p className="mt-1 text-sm text-red-700 dark:text-red-300">
                  {error.message}
                </p>
              )}
            </div>

            <Button
              variant="ghost"
              size="sm"
              onClick={onDismiss}
              className={`shrink-0 h-8 w-8 p-0 ${
                isRateLimit
                  ? "text-amber-600 hover:text-amber-800 hover:bg-amber-100 dark:text-amber-400 dark:hover:bg-amber-900/40"
                  : "text-red-600 hover:text-red-800 hover:bg-red-100 dark:text-red-400 dark:hover:bg-red-900/40"
              }`}
            >
              <X className="h-4 w-4" />
              <span className="sr-only">Dismiss</span>
            </Button>
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
