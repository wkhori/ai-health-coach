import { AdherenceStats as AdherenceStatsType } from "@/lib/types";
import {
  Flame,
  TrendingDown,
  TrendingUp,
  Minus,
  BarChart3,
  Sparkles,
} from "lucide-react";

function TrendIcon({ trend }: { trend: AdherenceStatsType["trend"] }) {
  switch (trend) {
    case "up":
      return <TrendingUp className="size-3.5 text-emerald-500" />;
    case "down":
      return <TrendingDown className="size-3.5 text-red-500" />;
    case "stable":
      return <Minus className="size-3.5 text-muted-foreground" />;
  }
}

function EmptyState() {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-dashed border-muted-foreground/25 p-3">
      <div className="flex size-8 shrink-0 items-center justify-center rounded-md bg-emerald-100 dark:bg-emerald-950">
        <Sparkles className="size-4 text-emerald-500" />
      </div>
      <p className="text-xs leading-relaxed text-muted-foreground">
        Start chatting with the coach to begin tracking your progress!
      </p>
    </div>
  );
}

export function AdherenceStats({ stats }: { stats: AdherenceStatsType }) {
  const isEmpty = stats.streak === 0 && stats.weeklyCompletion === 0;

  if (isEmpty) {
    return <EmptyState />;
  }

  return (
    <div className="grid grid-cols-2 gap-3">
      <div className="flex items-center gap-2.5 rounded-lg bg-muted/50 p-2.5">
        <div className="flex size-8 items-center justify-center rounded-md bg-amber-100 dark:bg-amber-950">
          <Flame className="size-4 text-amber-500" />
        </div>
        <div>
          <p className="text-lg font-semibold leading-none">{stats.streak}</p>
          <p className="text-[11px] text-muted-foreground">day streak</p>
        </div>
      </div>
      <div className="flex items-center gap-2.5 rounded-lg bg-muted/50 p-2.5">
        <div className="flex size-8 items-center justify-center rounded-md bg-blue-100 dark:bg-blue-950">
          <BarChart3 className="size-4 text-blue-500" />
        </div>
        <div className="flex items-center gap-1">
          <div>
            <p className="text-lg font-semibold leading-none">
              {stats.weeklyCompletion}%
            </p>
            <p className="text-[11px] text-muted-foreground">this week</p>
          </div>
          <TrendIcon trend={stats.trend} />
        </div>
      </div>
    </div>
  );
}
