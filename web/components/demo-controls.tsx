"use client";

import { useState } from "react";
import { PhaseBadge } from "@/components/sidebar/phase-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { Phase, SafetyResult, ToolCall } from "@/lib/types";
import { cn } from "@/lib/utils";
import {
  ChevronLeft,
  ChevronRight,
  Shield,
  Wrench,
  RotateCcw,
  Radio,
  Loader2,
} from "lucide-react";

const ACTION_CONFIG: Record<string, { label: string; className: string }> = {
  passed: {
    label: "PASSED",
    className:
      "border-emerald-300 bg-emerald-50 text-emerald-700 dark:border-emerald-700 dark:bg-emerald-950/30 dark:text-emerald-300",
  },
  rewritten: {
    label: "REWRITTEN",
    className:
      "border-amber-300 bg-amber-50 text-amber-700 dark:border-amber-700 dark:bg-amber-950/30 dark:text-amber-300",
  },
  blocked: {
    label: "BLOCKED",
    className:
      "border-red-300 bg-red-50 text-red-700 dark:border-red-700 dark:bg-red-950/30 dark:text-red-300",
  },
  escalated: {
    label: "ESCALATED",
    className:
      "border-red-400 bg-red-100 text-red-800 dark:border-red-600 dark:bg-red-950/50 dark:text-red-200",
  },
};

interface DemoControlsProps {
  phase: Phase;
  safetyResult: SafetyResult | null;
  toolCalls: ToolCall[];
  demoMode: boolean;
  onReset: () => void;
}

export function DemoControls({
  phase,
  safetyResult,
  toolCalls,
  demoMode,
  onReset,
}: DemoControlsProps) {
  const [open, setOpen] = useState(false);
  const [resetting, setResetting] = useState(false);

  const handleReset = async () => {
    setResetting(true);
    try {
      await onReset();
    } finally {
      setResetting(false);
    }
  };

  return (
    <>
      {/* Toggle button */}
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className={cn(
          "fixed right-0 top-1/2 z-50 -translate-y-1/2 rounded-l-lg border border-r-0 bg-background/95 px-1 py-3 shadow-md backdrop-blur transition-all hover:bg-accent hidden sm:block",
          open && "right-72"
        )}
        title={open ? "Close demo controls" : "Open demo controls"}
      >
        {open ? (
          <ChevronRight className="size-4 text-muted-foreground" />
        ) : (
          <ChevronLeft className="size-4 text-muted-foreground" />
        )}
      </button>

      {/* Panel */}
      <div
        className={cn(
          "fixed right-0 top-13 bottom-0 z-40 w-72 border-l bg-background/95 backdrop-blur transition-transform duration-200 ease-in-out hidden sm:block",
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        <ScrollArea className="h-full">
          <div className="space-y-4 p-4">
            {/* Header */}
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-semibold">Demo Controls</h3>
              <Badge
                variant="outline"
                className={cn(
                  "text-[10px]",
                  demoMode
                    ? "border-amber-300 text-amber-600 dark:border-amber-700 dark:text-amber-400"
                    : "border-emerald-300 text-emerald-600 dark:border-emerald-700 dark:text-emerald-400"
                )}
              >
                <Radio className="mr-1 size-2.5" />
                {demoMode ? "DEMO" : "LIVE"}
              </Badge>
            </div>

            {/* Current Phase */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-xs font-medium text-muted-foreground">
                  Current Phase
                </CardTitle>
              </CardHeader>
              <CardContent>
                <PhaseBadge phase={phase} />
              </CardContent>
            </Card>

            {/* Safety Result */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <Shield className="size-3" />
                  Safety Result
                </CardTitle>
              </CardHeader>
              <CardContent>
                {safetyResult ? (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge
                        variant="outline"
                        className={
                          ACTION_CONFIG[safetyResult.action ?? "passed"]
                            ?.className ?? ""
                        }
                      >
                        {ACTION_CONFIG[safetyResult.action ?? "passed"]
                          ?.label ?? "UNKNOWN"}
                      </Badge>
                    </div>
                    <div className="space-y-1 text-xs">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          Classification
                        </span>
                        <span className="font-medium">
                          {safetyResult.classification}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground">
                          Confidence
                        </span>
                        <span className="font-medium">
                          {(safetyResult.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground/60">
                    No classification yet
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Tool Calls */}
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center gap-1.5 text-xs font-medium text-muted-foreground">
                  <Wrench className="size-3" />
                  Tool Calls
                  {toolCalls.length > 0 && (
                    <Badge variant="secondary" className="ml-auto text-[10px]">
                      {toolCalls.length}
                    </Badge>
                  )}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {toolCalls.length > 0 ? (
                  <div className="space-y-1.5">
                    {toolCalls.map((tc, i) => (
                      <div
                        key={i}
                        className="flex items-center gap-2 text-xs"
                      >
                        <span
                          className={cn(
                            "size-1.5 shrink-0 rounded-full",
                            tc.status === "complete"
                              ? "bg-emerald-500"
                              : tc.status === "running"
                                ? "bg-blue-500"
                                : "bg-muted-foreground/30"
                          )}
                        />
                        <span className="font-mono font-medium">
                          {tc.tool}
                        </span>
                        <span className="ml-auto text-[10px] text-muted-foreground">
                          {tc.status}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-muted-foreground/60">
                    No tool calls yet
                  </p>
                )}
              </CardContent>
            </Card>

            {/* Reset */}
            <Button
              variant="outline"
              size="sm"
              className="w-full gap-1.5"
              onClick={handleReset}
              disabled={resetting}
            >
              {resetting ? (
                <Loader2 className="size-3.5 animate-spin" />
              ) : (
                <RotateCcw className="size-3.5" />
              )}
              Reset Demo
            </Button>
          </div>
        </ScrollArea>
      </div>
    </>
  );
}
