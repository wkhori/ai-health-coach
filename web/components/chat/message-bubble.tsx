import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Message } from "@/lib/types";
import { cn } from "@/lib/utils";
import { ToolCallCard } from "./tool-call-card";
import { TypingIndicator } from "./typing-indicator";
import { Heart, ShieldCheck } from "lucide-react";

function FormatContent({ content, isUser }: { content: string; isUser: boolean }) {
  if (isUser) {
    return <p className="whitespace-pre-wrap">{content}</p>;
  }

  // Simple markdown-like formatting for assistant messages
  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let listItems: React.ReactNode[] = [];
  let listType: "ul" | "ol" | null = null;

  const flushList = () => {
    if (listItems.length > 0) {
      if (listType === "ul") {
        elements.push(
          <ul key={`list-${elements.length}`} className="ml-4 list-disc space-y-0.5">
            {listItems}
          </ul>
        );
      } else {
        elements.push(
          <ol key={`list-${elements.length}`} className="ml-4 list-decimal space-y-0.5">
            {listItems}
          </ol>
        );
      }
      listItems = [];
      listType = null;
    }
  };

  const formatInline = (text: string) => {
    // Handle **bold**
    const parts = text.split(/(\*\*[^*]+\*\*)/g);
    return parts.map((part, i) => {
      if (part.startsWith("**") && part.endsWith("**")) {
        return <strong key={i}>{part.slice(2, -2)}</strong>;
      }
      return part;
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const bulletMatch = line.match(/^[\s]*[-•]\s+(.+)/);
    const numberedMatch = line.match(/^[\s]*\d+\.\s+(.+)/);

    if (bulletMatch) {
      if (listType !== "ul") flushList();
      listType = "ul";
      listItems.push(<li key={`li-${i}`}>{formatInline(bulletMatch[1])}</li>);
    } else if (numberedMatch) {
      if (listType !== "ol") flushList();
      listType = "ol";
      listItems.push(<li key={`li-${i}`}>{formatInline(numberedMatch[1])}</li>);
    } else {
      flushList();
      if (line.trim() === "") {
        elements.push(<br key={`br-${i}`} />);
      } else {
        elements.push(
          <p key={`p-${i}`} className={i > 0 ? "mt-1" : ""}>
            {formatInline(line)}
          </p>
        );
      }
    }
  }
  flushList();

  return <div className="space-y-1">{elements}</div>;
}

export function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const isStreaming = message.isStreaming && message.content === "";

  return (
    <div
      className={cn(
        "flex gap-3 animate-in fade-in-0 slide-in-from-bottom-2 duration-300",
        isUser ? "flex-row-reverse" : "flex-row"
      )}
    >
      <Avatar size="sm" className="mt-0.5 shrink-0">
        <AvatarFallback
          className={cn(
            "text-[10px] font-medium",
            isUser
              ? "bg-zinc-200 text-zinc-700 dark:bg-zinc-700 dark:text-zinc-200"
              : "bg-emerald-100 text-emerald-700 dark:bg-emerald-900 dark:text-emerald-300"
          )}
        >
          {isUser ? "You" : <Heart className="size-3" />}
        </AvatarFallback>
      </Avatar>

      <div
        className={cn(
          "flex max-w-[80%] flex-col gap-1",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed",
            isUser
              ? "rounded-tr-sm bg-emerald-600 text-white dark:bg-emerald-700"
              : "rounded-tl-sm bg-muted/80 text-foreground"
          )}
        >
          {isStreaming ? (
            <TypingIndicator />
          ) : (
            <FormatContent content={message.content} isUser={isUser} />
          )}
        </div>

        {message.tool_calls?.map((tc, i) => (
          <div key={i} className="w-full max-w-sm">
            <ToolCallCard toolCall={tc} />
          </div>
        ))}

        <div className="flex items-center gap-1.5 px-1">
          {!isUser && !message.isStreaming && message.content && (
            <span className="flex items-center gap-0.5 text-[10px] text-emerald-500/70">
              <ShieldCheck className="size-2.5" />
              <span>safe</span>
            </span>
          )}
          <time className="text-[10px] text-muted-foreground/60">
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </time>
        </div>
      </div>
    </div>
  );
}
