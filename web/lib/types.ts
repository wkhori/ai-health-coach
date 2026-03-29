// ─── Core UI types (used by all components) ─────────────────────

export type Phase = "PENDING" | "ONBOARDING" | "ACTIVE" | "RE_ENGAGING" | "DORMANT";

export interface Milestone {
  title: string;
  week: number;
  completed: boolean;
}

export interface Goal {
  id: string;
  title: string;
  status: "active" | "paused" | "completed";
  confirmed: boolean;
  milestones: Milestone[];
}

export interface AdherenceStats {
  streak: number;
  weeklyCompletion: number;
  trend: "up" | "down" | "stable";
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  phase?: Phase;
  created_at: string;
  tool_calls?: ToolCall[];
  isStreaming?: boolean;
}

export interface ToolCall {
  tool: string;
  args: Record<string, unknown>;
  result?: Record<string, unknown> | string;
  status: "pending" | "running" | "complete";
}

// ─── Demo mode types ─────────────────────────────────────────────

export interface Patient {
  id: string;
  name: string;
  phase: Phase;
  goals: Goal[];
  adherence: AdherenceStats;
  conversation: Message[];
  consentGiven: boolean;
}

// ─── SSE event types (shared between demo and real mode) ─────────

export interface SSEEvent {
  type: "token" | "tool_start" | "tool_end" | "phase_change" | "done" | "error";
  content?: string;
  tool?: string;
  args?: Record<string, unknown>;
  result?: Record<string, unknown> | string;
  from?: Phase;
  to?: Phase;
  phase?: Phase;
  message?: string;
  usage?: Record<string, unknown>;
}
