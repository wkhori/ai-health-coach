"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ShieldCheck, Loader2 } from "lucide-react";

interface ConsentBannerProps {
  onConsent: () => void | Promise<void>;
}

export function ConsentBanner({ onConsent }: ConsentBannerProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleClick = async () => {
    setLoading(true);
    setError(null);
    try {
      await onConsent();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to grant consent");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border-b bg-amber-50/80 dark:bg-amber-950/20">
      <div className="mx-auto flex max-w-3xl items-start gap-3 px-4 py-3 sm:items-center sm:gap-4 sm:py-4">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-amber-100 dark:bg-amber-900">
          <ShieldCheck className="size-5 text-amber-600 dark:text-amber-400" />
        </div>
        <div className="flex flex-1 flex-col gap-2 sm:flex-row sm:items-center sm:gap-4">
          <div className="min-w-0 flex-1">
            <p className="text-sm font-medium text-amber-900 dark:text-amber-100">
              AI Wellness Coach
            </p>
            <p className="text-xs text-amber-700 dark:text-amber-300">
              This coach provides general wellness guidance for your exercise
              program. It does not provide medical advice. By consenting, you
              agree to receive coaching messages.
            </p>
            {error && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">
                {error}
              </p>
            )}
          </div>
          <Button
            onClick={handleClick}
            disabled={loading}
            size="sm"
            className="w-fit shrink-0 bg-amber-600 text-white hover:bg-amber-700 dark:bg-amber-700 dark:hover:bg-amber-600"
          >
            {loading ? (
              <>
                <Loader2 className="mr-1.5 size-3.5 animate-spin" />
                Granting...
              </>
            ) : (
              "I agree to receive coaching"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
