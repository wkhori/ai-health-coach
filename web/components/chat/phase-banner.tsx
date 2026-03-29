import { Phase } from "@/lib/types";
import { ArrowRight, Sparkles } from "lucide-react";
import { PhaseBadge } from "@/components/sidebar/phase-badge";

const TRANSITION_TEXT: Record<string, string> = {
  "PENDING_ONBOARDING": "Consent accepted! Let's set your first goal.",
  "ONBOARDING_ACTIVE": "Your goals are set! Time to start tracking progress.",
  "ACTIVE_RE_ENGAGING": "We noticed you've been away. Let's get back on track!",
  "RE_ENGAGING_ACTIVE": "Welcome back! Your program is active again.",
  "RE_ENGAGING_DORMANT": "Your program has been paused. Send a message to restart anytime.",
  "DORMANT_RE_ENGAGING": "Great to see you! Let's restart your program.",
};

export function PhaseBanner({ from, to }: { from: Phase; to: Phase }) {
  const key = `${from}_${to}`;
  const text = TRANSITION_TEXT[key] ?? `Moved from ${from} to ${to}`;

  return (
    <div className="mx-auto my-4 max-w-sm space-y-1.5 rounded-xl bg-gradient-to-r from-emerald-50 to-blue-50 px-4 py-3 text-center dark:from-emerald-950/30 dark:to-blue-950/30">
      <div className="flex items-center justify-center gap-2 text-xs text-muted-foreground">
        <Sparkles className="size-3 text-emerald-500" />
        <span className="font-medium">Phase transition</span>
      </div>
      <div className="flex items-center justify-center gap-2">
        <PhaseBadge phase={from} />
        <ArrowRight className="size-3 text-muted-foreground" />
        <PhaseBadge phase={to} />
      </div>
      <p className="text-xs text-muted-foreground">{text}</p>
    </div>
  );
}
