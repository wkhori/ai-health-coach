"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { MessageBubble } from "./message-bubble";
import { MessageInput } from "./message-input";
import { PhaseBanner } from "./phase-banner";
import { EmptyState } from "./empty-state";
import { SuggestedPrompts } from "./suggested-prompts";
import { Message, Phase, ToolCall, SSEEvent, SafetyResult } from "@/lib/types";
import { demoResponses, simulateStream } from "@/lib/demo-responses";
import { streamChat } from "@/lib/api";

interface ChatContainerProps {
  patientId: string;
  initialMessages: Message[];
  disabled?: boolean;
  demoMode?: boolean;
  phase?: Phase;
  onGoalsChanged?: () => void;
  onPhaseChanged?: () => void;
  onSafetyResult?: (result: SafetyResult) => void;
  onToolCall?: (toolCall: ToolCall) => void;
}

export function ChatContainer({
  patientId,
  initialMessages,
  disabled,
  demoMode,
  phase = "ACTIVE",
  onGoalsChanged,
  onPhaseChanged,
  onSafetyResult,
  onToolCall,
}: ChatContainerProps) {
  const [messages, setMessages] = useState<Message[]>(initialMessages);
  const [isStreaming, setIsStreaming] = useState(false);
  const [responseIndex, setResponseIndex] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);
  const prevPatientId = useRef(patientId);
  const abortRef = useRef<AbortController | null>(null);
  const hasSentMessage = useRef(false);

  // Reset when patient changes
  useEffect(() => {
    if (prevPatientId.current !== patientId) {
      setMessages(initialMessages);
      setIsStreaming(false);
      setResponseIndex(0);
      prevPatientId.current = patientId;
      hasSentMessage.current = false;
    }
  }, [patientId, initialMessages]);

  // Sync initial messages when they change from parent (only before user sends)
  useEffect(() => {
    if (!isStreaming && !hasSentMessage.current) {
      setMessages(initialMessages);
    }
  }, [initialMessages, isStreaming]);

  // Auto-scroll
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isStreaming]);

  // Cleanup abort controller on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
    };
  }, []);

  // ── Demo mode send handler ─────────────────────────────────────
  const handleDemoSend = useCallback(
    async (text: string) => {
      hasSentMessage.current = true;
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);

      const responses = demoResponses[patientId] || demoResponses.sarah;
      const response = responses[responseIndex % responses.length];
      setResponseIndex((i) => i + 1);

      const assistantId = `msg-${Date.now()}-assistant`;
      const assistantMessage: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsStreaming(true);

      // Simulate tool calls
      if (response.toolCalls && response.toolCalls.length > 0) {
        for (const tc of response.toolCalls) {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    tool_calls: [
                      ...(m.tool_calls || []),
                      { ...tc, status: "running" as const, result: undefined },
                    ],
                  }
                : m
            )
          );

          await new Promise((resolve) => setTimeout(resolve, 800));

          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    tool_calls: (m.tool_calls || []).map((t) =>
                      t.tool === tc.tool
                        ? {
                            ...t,
                            status: "complete" as const,
                            result: tc.result,
                          }
                        : t
                    ),
                  }
                : m
            )
          );

          await new Promise((resolve) => setTimeout(resolve, 300));
        }
      }

      // Stream text
      await simulateStream(response.content, (token) => {
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId
              ? { ...m, content: m.content + token, isStreaming: true }
              : m
          )
        );
      });

      // Finalize
      setMessages((prev) =>
        prev.map((m) =>
          m.id === assistantId ? { ...m, isStreaming: false } : m
        )
      );

      // Emit demo safety result
      onSafetyResult?.({
        classification: "safe",
        confidence: 0.99,
        categories: ["general_wellness"],
        action: "passed",
        reasoning: "Demo mode — auto pass",
      });

      // Emit demo tool calls
      if (response.toolCalls) {
        for (const tc of response.toolCalls) {
          onToolCall?.({
            tool: tc.tool,
            args: tc.args ?? {},
            result: tc.result,
            status: "complete",
          });
        }
      }

      // Phase change
      if (response.phaseChange) {
        await new Promise((resolve) => setTimeout(resolve, 500));
        setMessages((prev) => [
          ...prev,
          {
            id: `phase-${Date.now()}`,
            role: "assistant",
            content: `__PHASE_CHANGE__${response.phaseChange!.from}__${response.phaseChange!.to}__`,
            created_at: new Date().toISOString(),
          },
        ]);
      }

      setIsStreaming(false);
    },
    [patientId, responseIndex, onSafetyResult, onToolCall]
  );

  // ── Real mode send handler (SSE streaming) ─────────────────────
  const handleRealSend = useCallback(
    async (text: string) => {
      hasSentMessage.current = true;
      const userMessage: Message = {
        id: `msg-${Date.now()}`,
        role: "user",
        content: text,
        created_at: new Date().toISOString(),
      };

      setMessages((prev) => [...prev, userMessage]);

      const assistantId = `msg-${Date.now()}-assistant`;
      const assistantMessage: Message = {
        id: assistantId,
        role: "assistant",
        content: "",
        created_at: new Date().toISOString(),
        isStreaming: true,
      };

      setMessages((prev) => [...prev, assistantMessage]);
      setIsStreaming(true);

      const abortController = new AbortController();
      abortRef.current = abortController;

      try {
        await streamChat(
          text,
          (event: SSEEvent) => {
            switch (event.type) {
              case "token":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          content: m.content + (event.content ?? ""),
                          isStreaming: true,
                        }
                      : m
                  )
                );
                break;

              case "tool_start":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          tool_calls: [
                            ...(m.tool_calls || []),
                            {
                              tool: event.tool ?? "unknown",
                              args: event.args ?? {},
                              status: "running" as const,
                            },
                          ],
                        }
                      : m
                  )
                );
                break;

              case "tool_end": {
                const toolResult =
                  typeof event.result === "string"
                    ? { output: event.result }
                    : ((event.result as Record<string, unknown>) ?? {});
                setMessages((prev) =>
                  prev.map((m) => {
                    if (m.id !== assistantId) return m;
                    const toolCalls = (m.tool_calls || []).map(
                      (tc: ToolCall) =>
                        tc.tool === event.tool && tc.status === "running"
                          ? {
                              ...tc,
                              status: "complete" as const,
                              result: toolResult,
                            }
                          : tc
                    );
                    return { ...m, tool_calls: toolCalls };
                  })
                );
                // Notify parent of tool call completion
                onToolCall?.({
                  tool: event.tool ?? "unknown",
                  args: event.args ?? {},
                  result: toolResult,
                  status: "complete",
                });
                // Refetch goals after set_goal tool completes
                if (event.tool === "set_goal") {
                  onGoalsChanged?.();
                }
                break;
              }

              case "phase_change": {
                // Backend may send {phase: "X"} or {from: "X", to: "Y"}
                const fromPhase = event.from ?? phase;
                const toPhase = event.to ?? event.phase ?? phase;
                if (fromPhase !== toPhase) {
                  setMessages((prev) => [
                    ...prev.map((m) =>
                      m.id === assistantId
                        ? { ...m, isStreaming: false }
                        : m
                    ),
                    {
                      id: `phase-${Date.now()}`,
                      role: "assistant" as const,
                      content: `__PHASE_CHANGE__${fromPhase}__${toPhase}__`,
                      created_at: new Date().toISOString(),
                    },
                  ]);
                  onPhaseChanged?.();
                }
                break;
              }

              case "safety_result": {
                const sr = event.result as Record<string, unknown> | undefined;
                if (sr) {
                  onSafetyResult?.({
                    classification: (sr.classification as string) ?? "unknown",
                    confidence: (sr.confidence as number) ?? 0,
                    categories: sr.categories as string[] | undefined,
                    action: sr.action_taken as SafetyResult["action"],
                    reasoning: sr.reasoning as string | undefined,
                  });
                }
                break;
              }

              case "done":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? { ...m, isStreaming: false }
                      : m
                  )
                );
                onGoalsChanged?.();
                break;

              case "error":
                setMessages((prev) =>
                  prev.map((m) =>
                    m.id === assistantId
                      ? {
                          ...m,
                          content:
                            m.content ||
                            event.message ||
                            "Something went wrong. Please try again.",
                          isStreaming: false,
                        }
                      : m
                  )
                );
                break;
            }
          },
          abortController.signal
        );

        // Ensure streaming is finalized
        setMessages((prev) =>
          prev.map((m) =>
            m.id === assistantId ? { ...m, isStreaming: false } : m
          )
        );
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          setMessages((prev) =>
            prev.map((m) =>
              m.id === assistantId
                ? {
                    ...m,
                    content:
                      m.content ||
                      "Failed to connect to the server. Please try again.",
                    isStreaming: false,
                  }
                : m
            )
          );
        }
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [phase, onGoalsChanged, onPhaseChanged, onSafetyResult, onToolCall]
  );

  // ── Dispatch to correct handler ────────────────────────────────
  const handleSend = useCallback(
    async (text: string) => {
      if (isStreaming || disabled) return;
      if (demoMode) {
        await handleDemoSend(text);
      } else {
        await handleRealSend(text);
      }
    },
    [isStreaming, disabled, demoMode, handleDemoSend, handleRealSend]
  );

  // Check if we should show suggested prompts (after last assistant message, not streaming)
  const lastMessage = messages[messages.length - 1];
  const showSuggestions =
    !isStreaming &&
    !disabled &&
    messages.length > 0 &&
    lastMessage?.role === "assistant" &&
    !lastMessage.content.startsWith("__PHASE_CHANGE__");

  return (
    <div className="flex h-full flex-col">
      <ScrollArea className="flex-1 overflow-hidden">
        <div className="mx-auto max-w-2xl space-y-4 px-4 py-6">
          {messages.length === 0 ? (
            <EmptyState
              phase={phase}
              onPromptSelect={handleSend}
              disabled={disabled}
            />
          ) : (
            <>
              {messages.map((message) => {
                if (message.content.startsWith("__PHASE_CHANGE__")) {
                  const parts = message.content.split("__");
                  const from = parts[2] as Phase;
                  const to = parts[3] as Phase;
                  return <PhaseBanner key={message.id} from={from} to={to} />;
                }
                return <MessageBubble key={message.id} message={message} />;
              })}
              {showSuggestions && (
                <div className="pt-2">
                  <SuggestedPrompts
                    phase={phase}
                    onSelect={handleSend}
                    disabled={disabled}
                  />
                </div>
              )}
            </>
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="border-t bg-background/95 px-4 py-3 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="mx-auto max-w-2xl">
          <MessageInput
            onSend={handleSend}
            disabled={isStreaming || disabled}
            placeholder={
              disabled
                ? "Accept consent to start chatting..."
                : isStreaming
                  ? "Waiting for response..."
                  : phase === "ONBOARDING"
                    ? "Tell me about your exercise goals..."
                    : phase === "RE_ENGAGING"
                      ? "Ready to get back on track?"
                      : "How's your progress today?"
            }
          />
          <p className="mt-1.5 text-center text-[10px] text-muted-foreground/50">
            AI wellness coach. Not a substitute for medical advice.
          </p>
        </div>
      </div>
    </div>
  );
}
