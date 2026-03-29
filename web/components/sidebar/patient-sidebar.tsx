"use client";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import { PhaseBadge } from "./phase-badge";
import { GoalCard } from "./goal-card";
import { AdherenceStats } from "./adherence-stats";
import type {
  Phase,
  Goal,
  AdherenceStats as AdherenceStatsType,
} from "@/lib/types";
import {
  Activity,
  ShieldCheck,
  Rocket,
  Target,
  HandMetal,
  Moon,
} from "lucide-react";

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

const phaseMotivation: Record<Phase, string> = {
  PENDING: "Complete consent to begin your wellness journey",
  ONBOARDING: "Let's set your first exercise goal!",
  ACTIVE: "Keep up the great work!",
  RE_ENGAGING: "Welcome back! Let's pick up where you left off",
  DORMANT: "Ready to restart? Send a message to your coach",
};

const phaseEmptyMessages: Record<Phase, string> = {
  PENDING: "Grant consent to get started with your wellness journey",
  ONBOARDING: "Chat with the coach to set your first goal!",
  ACTIVE: "Your goals will appear here as you set them",
  RE_ENGAGING: "Welcome back! Let's review your previous goals",
  DORMANT: "Your goals will be here when you return",
};

const phaseEmptyIcons: Record<Phase, React.ReactNode> = {
  PENDING: <ShieldCheck className="size-5 text-zinc-400" />,
  ONBOARDING: <Rocket className="size-5 text-blue-400" />,
  ACTIVE: <Target className="size-5 text-emerald-400" />,
  RE_ENGAGING: <HandMetal className="size-5 text-amber-400" />,
  DORMANT: <Moon className="size-5 text-red-400" />,
};

interface PatientSidebarProps {
  name: string;
  phase: Phase;
  goals: Goal[];
  adherence: AdherenceStatsType;
}

export function PatientSidebar({
  name,
  phase,
  goals,
  adherence,
}: PatientSidebarProps) {
  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 p-4 pb-3">
        <Avatar size="lg">
          <AvatarFallback className="bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300">
            {getInitials(name)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-0 flex-1">
          <h2 className="truncate text-sm font-semibold">{name}</h2>
          <div className="mt-1 flex items-center gap-2">
            <PhaseBadge phase={phase} />
          </div>
          <p className="mt-0.5 text-[11px] text-muted-foreground">
            {phaseMotivation[phase]}
          </p>
        </div>
      </div>

      <Separator />

      <ScrollArea className="flex-1 overflow-auto">
        <div className="space-y-4 p-4">
          <div>
            <h3 className="mb-2.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
              <Activity className="size-3.5" />
              Quick Stats
            </h3>
            <AdherenceStats stats={adherence} />
          </div>

          {goals.length > 0 && (
            <div>
              <Separator className="mb-4" />
              <h3 className="mb-2.5 flex items-center gap-1.5 text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Goals
                <Badge
                  variant="secondary"
                  className="ml-1 px-1.5 py-0 text-[10px] font-semibold leading-4"
                >
                  {goals.length}
                </Badge>
              </h3>
              <div className="space-y-3">
                {goals.map((goal) => (
                  <GoalCard key={goal.id} goal={goal} />
                ))}
              </div>
            </div>
          )}

          {goals.length === 0 && (
            <div className="rounded-lg border border-dashed p-4 text-center">
              <div className="mx-auto mb-2 flex size-9 items-center justify-center rounded-full bg-muted/70">
                {phaseEmptyIcons[phase]}
              </div>
              <p className="text-xs text-muted-foreground">
                {phaseEmptyMessages[phase]}
              </p>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
