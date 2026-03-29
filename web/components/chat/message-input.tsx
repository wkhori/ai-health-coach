"use client";

import { useState, useRef, useCallback, KeyboardEvent } from "react";
import { Button } from "@/components/ui/button";
import { SendHorizontal } from "lucide-react";
import { cn } from "@/lib/utils";

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({ onSend, disabled, placeholder }: MessageInputProps) {
  const [value, setValue] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = useCallback(() => {
    const trimmed = value.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setValue("");
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }
  }, [value, disabled, onSend]);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleInput = () => {
    const el = textareaRef.current;
    if (el) {
      el.style.height = "auto";
      el.style.height = Math.min(el.scrollHeight, 160) + "px";
    }
  };

  return (
    <div className="flex items-end gap-2 rounded-xl border bg-card p-2 shadow-sm transition-colors focus-within:border-emerald-300 dark:focus-within:border-emerald-700">
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => {
          setValue(e.target.value);
          handleInput();
        }}
        onKeyDown={handleKeyDown}
        placeholder={placeholder ?? "Type your message..."}
        disabled={disabled}
        rows={1}
        className={cn(
          "flex-1 resize-none bg-transparent px-2 py-1.5 text-sm leading-relaxed outline-none placeholder:text-muted-foreground/60 disabled:cursor-not-allowed disabled:opacity-50"
        )}
      />
      <Button
        onClick={handleSend}
        disabled={disabled || !value.trim()}
        size="icon-sm"
        className="shrink-0 rounded-lg bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-40 dark:bg-emerald-700 dark:hover:bg-emerald-600"
      >
        <SendHorizontal className="size-4" />
        <span className="sr-only">Send message</span>
      </Button>
    </div>
  );
}
