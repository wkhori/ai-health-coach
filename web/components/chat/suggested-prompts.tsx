"use client";

import { Button } from "@/components/ui/button";
import type { Phase } from "@/lib/types";
import { MessageCircle, Target, BarChart3, RefreshCcw } from "lucide-react";

const PROMPTS: Record<string, { text: string; icon: typeof MessageCircle }[]> = {
  ONBOARDING: [
    { text: "I'd like to set a fitness goal", icon: Target },
    { text: "What activities do you recommend?", icon: MessageCircle },
    { text: "How does goal tracking work?", icon: BarChart3 },
  ],
  ACTIVE: [
    { text: "How am I doing this week?", icon: BarChart3 },
    { text: "I completed today's exercise!", icon: Target },
    { text: "Can we adjust my goals?", icon: RefreshCcw },
    { text: "Show me my program summary", icon: MessageCircle },
  ],
  RE_ENGAGING: [
    { text: "I'm ready to get back on track", icon: RefreshCcw },
    { text: "What's my current program?", icon: MessageCircle },
    { text: "Let's update my goals", icon: Target },
  ],
  DORMANT: [
    { text: "I want to restart my program", icon: RefreshCcw },
    { text: "What were my previous goals?", icon: Target },
  ],
};

interface SuggestedPromptsProps {
  phase: Phase;
  onSelect: (text: string) => void;
  disabled?: boolean;
}

export function SuggestedPrompts({
  phase,
  onSelect,
  disabled,
}: SuggestedPromptsProps) {
  const prompts = PROMPTS[phase] ?? PROMPTS.ACTIVE;

  return (
    <div className="flex flex-wrap gap-2">
      {prompts.map(({ text, icon: Icon }) => (
        <Button
          key={text}
          variant="outline"
          size="sm"
          disabled={disabled}
          onClick={() => onSelect(text)}
          className="gap-1.5 rounded-full text-xs font-normal text-muted-foreground hover:text-foreground"
        >
          <Icon className="size-3" />
          {text}
        </Button>
      ))}
    </div>
  );
}
