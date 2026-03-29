import { Badge } from "@/components/ui/badge";
import { Phase } from "@/lib/types";
import { cn } from "@/lib/utils";

const phaseConfig: Record<
  Phase,
  { label: string; className: string }
> = {
  PENDING: {
    label: "Pending",
    className: "bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-400",
  },
  ONBOARDING: {
    label: "Onboarding",
    className:
      "bg-blue-50 text-blue-700 dark:bg-blue-950 dark:text-blue-300",
  },
  ACTIVE: {
    label: "Active",
    className:
      "bg-emerald-50 text-emerald-700 dark:bg-emerald-950 dark:text-emerald-300",
  },
  RE_ENGAGING: {
    label: "Re-engaging",
    className:
      "bg-amber-50 text-amber-700 dark:bg-amber-950 dark:text-amber-300",
  },
  DORMANT: {
    label: "Dormant",
    className: "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300",
  },
};

export function PhaseBadge({ phase }: { phase: Phase }) {
  const config = phaseConfig[phase];
  return (
    <Badge
      variant="secondary"
      className={cn(
        "border-0 text-xs font-medium",
        config.className
      )}
    >
      {config.label}
    </Badge>
  );
}
