"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Goal } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  CheckCircle2,
  Circle,
  Target,
  ChevronDown,
  ChevronRight,
  Clock,
} from "lucide-react";

const WEEK_LABELS = ["Foundation", "Building", "Strengthening", "Achievement"];

function MilestoneTimeline({
  milestones,
}: {
  milestones: Goal["milestones"];
}) {
  const completed = milestones.filter((m) => m.completed).length;
  const total = milestones.length;
  const percent = total > 0 ? (completed / total) * 100 : 0;
  const currentIndex = milestones.findIndex((m) => !m.completed);

  return (
    <div className="space-y-2">
      {/* Progress bar */}
      <div className="flex items-center justify-between text-xs text-muted-foreground">
        <span>
          {completed} of {total} milestones
        </span>
        <span>{Math.round(percent)}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
        <div
          className="h-full rounded-full bg-emerald-500 transition-all duration-500"
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Vertical timeline */}
      <div className="relative ml-1 mt-3">
        {milestones.map((milestone, i) => {
          const isCurrent = i === currentIndex;
          const isFuture = currentIndex >= 0 ? i > currentIndex : !milestone.completed;
          const weekLabel = WEEK_LABELS[milestone.week - 1] ?? `Week ${milestone.week}`;

          return (
            <div key={i} className="relative flex gap-3">
              {/* Connector line */}
              {i < milestones.length - 1 && (
                <div
                  className={cn(
                    "absolute left-[7px] top-[18px] w-0.5 h-[calc(100%-4px)]",
                    milestone.completed
                      ? "bg-emerald-400 dark:bg-emerald-600"
                      : "bg-muted"
                  )}
                />
              )}

              {/* Node */}
              <div className="relative z-10 shrink-0 pt-0.5">
                {milestone.completed ? (
                  <CheckCircle2 className="size-4 text-emerald-500" />
                ) : isCurrent ? (
                  <div className="flex size-4 items-center justify-center rounded-full border-2 border-emerald-500 bg-background">
                    <div className="size-1.5 rounded-full bg-emerald-500" />
                  </div>
                ) : (
                  <Circle className="size-4 text-muted-foreground/30" />
                )}
              </div>

              {/* Content */}
              <div
                className={cn(
                  "mb-3 flex-1 rounded-md px-2 py-1.5 transition-colors",
                  isCurrent && "bg-emerald-50 dark:bg-emerald-950/30"
                )}
              >
                <div className="flex items-center gap-1.5">
                  <span
                    className={cn(
                      "text-[10px] font-semibold uppercase tracking-wider",
                      milestone.completed
                        ? "text-emerald-600 dark:text-emerald-400"
                        : isCurrent
                          ? "text-emerald-600 dark:text-emerald-400"
                          : "text-muted-foreground/50"
                    )}
                  >
                    Wk {milestone.week}: {weekLabel}
                  </span>
                  {isCurrent && (
                    <span className="rounded-full bg-emerald-100 px-1.5 py-0.5 text-[9px] font-medium text-emerald-700 dark:bg-emerald-900/50 dark:text-emerald-300">
                      current
                    </span>
                  )}
                </div>
                <p
                  className={cn(
                    "mt-0.5 text-xs leading-tight",
                    milestone.completed
                      ? "text-muted-foreground line-through"
                      : isFuture
                        ? "text-muted-foreground/60"
                        : "text-foreground"
                  )}
                >
                  {milestone.title}
                </p>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export function GoalCard({ goal }: { goal: Goal }) {
  const [expanded, setExpanded] = useState(goal.milestones.length < 3);
  const completed = goal.milestones.filter((m) => m.completed).length;
  const total = goal.milestones.length;

  return (
    <Card
      size="sm"
      className={cn(
        "bg-card/50 transition-colors",
        !goal.confirmed &&
          "border-dashed border-amber-300 dark:border-amber-700"
      )}
    >
      <CardHeader className="pb-0">
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          className="flex w-full items-center gap-2 text-left"
        >
          {expanded ? (
            <ChevronDown className="size-3 shrink-0 text-muted-foreground" />
          ) : (
            <ChevronRight className="size-3 shrink-0 text-muted-foreground" />
          )}
          <Target className="size-3.5 shrink-0 text-emerald-600 dark:text-emerald-400" />
          <CardTitle className="flex-1 text-sm leading-snug">
            {goal.title}
          </CardTitle>
          <span
            className={cn(
              "size-2 shrink-0 rounded-full",
              goal.status === "active"
                ? "bg-emerald-500"
                : goal.status === "paused"
                  ? "bg-amber-500"
                  : "bg-zinc-400"
            )}
          />
        </button>
        {!goal.confirmed && (
          <Badge
            variant="outline"
            className="mt-1.5 w-fit border-amber-300 text-[10px] text-amber-600 dark:border-amber-700 dark:text-amber-400"
          >
            <Clock className="mr-1 size-2.5" />
            Awaiting confirmation
          </Badge>
        )}
      </CardHeader>
      <CardContent>
        {expanded ? (
          <MilestoneTimeline milestones={goal.milestones} />
        ) : (
          <p className="text-xs text-muted-foreground">
            {completed} of {total} milestones complete
          </p>
        )}
      </CardContent>
    </Card>
  );
}
