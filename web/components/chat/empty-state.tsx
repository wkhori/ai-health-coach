import { Heart, Sparkles } from "lucide-react";
import { SuggestedPrompts } from "./suggested-prompts";
import type { Phase } from "@/lib/types";

const GREETINGS: Record<string, { title: string; subtitle: string }> = {
  ONBOARDING: {
    title: "Welcome! I'm your wellness coach",
    subtitle:
      "I'll help you set exercise goals and build healthy habits. Let's start by talking about what kind of activities you enjoy.",
  },
  ACTIVE: {
    title: "Welcome back!",
    subtitle:
      "Ready to continue your wellness journey? Let me know how your exercises are going or if you'd like to adjust your goals.",
  },
  RE_ENGAGING: {
    title: "It's great to see you again!",
    subtitle:
      "No worries about the break. Let's pick up where we left off and get you back on track.",
  },
  DORMANT: {
    title: "Welcome back!",
    subtitle:
      "It's been a while! Whenever you're ready, we can restart your program or set new goals.",
  },
  PENDING: {
    title: "Welcome to Stride",
    subtitle:
      "Please accept the consent agreement above to begin your wellness journey.",
  },
};

interface EmptyStateProps {
  phase: Phase;
  onPromptSelect: (text: string) => void;
  disabled?: boolean;
}

export function EmptyState({
  phase,
  onPromptSelect,
  disabled,
}: EmptyStateProps) {
  const greeting = GREETINGS[phase] ?? GREETINGS.ACTIVE;

  return (
    <div className="flex h-full flex-col items-center justify-center px-4">
      <div className="max-w-md space-y-6 text-center">
        <div className="mx-auto flex size-16 items-center justify-center rounded-2xl bg-emerald-100 dark:bg-emerald-900">
          <Heart className="size-8 text-emerald-600 dark:text-emerald-400" />
        </div>

        <div className="space-y-2">
          <h2 className="text-lg font-semibold tracking-tight">
            {greeting.title}
          </h2>
          <p className="text-sm leading-relaxed text-muted-foreground">
            {greeting.subtitle}
          </p>
        </div>

        {phase !== "PENDING" && (
          <div className="space-y-3">
            <div className="flex items-center justify-center gap-1.5 text-xs text-muted-foreground/60">
              <Sparkles className="size-3" />
              <span>Try asking</span>
            </div>
            <SuggestedPrompts
              phase={phase}
              onSelect={onPromptSelect}
              disabled={disabled}
            />
          </div>
        )}
      </div>
    </div>
  );
}
