import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ToolCall } from "@/lib/types";
import { Wrench, Loader2, CheckCircle2 } from "lucide-react";
import { cn } from "@/lib/utils";

function StatusIcon({ status }: { status: ToolCall["status"] }) {
  switch (status) {
    case "pending":
      return <Loader2 className="size-3.5 animate-spin text-muted-foreground" />;
    case "running":
      return <Loader2 className="size-3.5 animate-spin text-blue-500" />;
    case "complete":
      return <CheckCircle2 className="size-3.5 text-emerald-500" />;
  }
}

function formatToolName(name: string): string {
  return name
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function ToolCallCard({ toolCall }: { toolCall: ToolCall }) {
  return (
    <Card
      size="sm"
      className={cn(
        "my-2 border-l-2 bg-muted/30",
        toolCall.status === "complete"
          ? "border-l-emerald-500"
          : "border-l-blue-500"
      )}
    >
      <CardHeader className="pb-0">
        <CardTitle className="flex items-center gap-2 text-xs">
          <Wrench className="size-3 text-muted-foreground" />
          <span className="font-medium">{formatToolName(toolCall.tool)}</span>
          <StatusIcon status={toolCall.status} />
        </CardTitle>
      </CardHeader>
      <CardContent>
        {toolCall.args && Object.keys(toolCall.args).length > 0 && (
          <div className="mt-1 space-y-1">
            {Object.entries(toolCall.args).map(([key, value]) => (
              <div key={key} className="flex items-start gap-1.5 text-xs">
                <Badge
                  variant="outline"
                  className="shrink-0 font-mono text-[10px]"
                >
                  {key}
                </Badge>
                <span className="text-muted-foreground break-all">
                  {typeof value === "string"
                    ? value
                    : JSON.stringify(value, null, 0)}
                </span>
              </div>
            ))}
          </div>
        )}
        {toolCall.result && toolCall.status === "complete" && (
          <div className="mt-2 rounded-md bg-emerald-50/50 p-2 font-mono text-[11px] text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
            {typeof toolCall.result === "string"
              ? toolCall.result
              : JSON.stringify(toolCall.result, null, 2)}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
