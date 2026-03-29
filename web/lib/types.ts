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

// ─── Dashboard types ─────────────────────────────────────────────

export interface DashboardPatient {
  user_id: string;
  profile_id: string;
  display_name: string;
  phase: Phase;
  last_message_at: string | null;
  active_goals_count: number;
  total_milestones: number;
  completed_milestones: number;
  adherence_pct: number;
  alerts_count: number;
}

export interface DashboardAlert {
  id: string;
  user_id: string;
  patient_name: string;
  alert_type: string;
  urgency: "routine" | "urgent";
  message: string;
  created_at: string;
}

// ─── Safety result (from SSE stream) ────────────────────────────

export interface SafetyResult {
  classification: string;
  confidence: number;
  categories?: string[];
  action?: "passed" | "rewritten" | "blocked" | "escalated";
  reasoning?: string;
}

// ─── SSE event types (shared between demo and real mode) ─────────

export interface SSEEvent {
  type:
    | "token"
    | "tool_start"
    | "tool_end"
    | "phase_change"
    | "done"
    | "error"
    | "safety_result";
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
