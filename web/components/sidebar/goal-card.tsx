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

function MilestoneProgress({ milestones }: { milestones: Goal["milestones"] }) {
  const completed = milestones.filter((m) => m.completed).length;
  const total = milestones.length;
  const percent = total > 0 ? (completed / total) * 100 : 0;
  // Find the current milestone (first incomplete)
  const currentIndex = milestones.findIndex((m) => !m.completed);

  return (
    <div className="space-y-2">
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
      <div className="space-y-1">
        {milestones.map((milestone, i) => (
          <div
            key={i}
            className={cn(
              "flex items-center gap-2 rounded-md px-1.5 py-0.5 text-xs transition-colors",
              i === currentIndex && "bg-emerald-50 dark:bg-emerald-950/30"
            )}
          >
            {milestone.completed ? (
              <CheckCircle2 className="size-3.5 shrink-0 text-emerald-500" />
            ) : i === currentIndex ? (
              <Circle className="size-3.5 shrink-0 text-emerald-500" />
            ) : (
              <Circle className="size-3.5 shrink-0 text-muted-foreground/30" />
            )}
            <span
              className={cn(
                "leading-tight",
                milestone.completed
                  ? "text-muted-foreground line-through"
                  : i === currentIndex
                    ? "font-medium text-foreground"
                    : "text-muted-foreground"
              )}
            >
              {milestone.title}
            </span>
            {i === currentIndex && !milestone.completed && (
              <span className="ml-auto text-[10px] text-emerald-600 dark:text-emerald-400">
                current
              </span>
            )}
          </div>
        ))}
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
          <CardTitle className="flex-1 truncate text-sm">
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
          <MilestoneProgress milestones={goal.milestones} />
        ) : (
          <p className="text-xs text-muted-foreground">
            {completed} of {total} milestones complete
          </p>
        )}
      </CardContent>
    </Card>
  );
}
