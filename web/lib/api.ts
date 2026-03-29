import type { Phase, Goal, Message, AdherenceStats, SSEEvent } from "./types";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "";

// ─── Auth helpers ───────────────────────────────────────────────

function getAuthHeaders(): Record<string, string> {
  const token =
    typeof window !== "undefined"
      ? localStorage.getItem("auth_token")
      : null;
  if (!token) {
    throw new Error("Not authenticated");
  }
  return {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  };
}

async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: { ...headers, ...options.headers },
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail ?? body.error ?? `Request failed with status ${res.status}`,
      res.status,
      body.code,
      body.detail
    );
  }
  return res.json() as Promise<T>;
}

// ─── Error class ────────────────────────────────────────────────

export class ApiError extends Error {
  status: number;
  code?: string;
  detail?: string;

  constructor(
    message: string,
    status: number,
    code?: string,
    detail?: string
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.detail = detail;
  }
}

// ─── Auth API functions ─────────────────────────────────────────

export async function authLogin(
  email: string,
  password: string
): Promise<{
  token: string;
  user: { id: string; email: string; name: string };
}> {
  const res = await fetch(`${API_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail ?? body.error ?? "Login failed",
      res.status
    );
  }
  const data = await res.json();
  localStorage.setItem("auth_token", data.token);
  // Backend returns user_id, map to id for frontend
  return {
    token: data.token,
    user: {
      id: data.user.user_id,
      email: data.user.email,
      name: data.user.name,
    },
  };
}

export async function authRegister(
  email: string,
  password: string,
  name: string = ""
): Promise<{
  token: string;
  user: { id: string; email: string; name: string };
}> {
  const res = await fetch(`${API_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail ?? body.error ?? "Registration failed",
      res.status
    );
  }
  const data = await res.json();
  localStorage.setItem("auth_token", data.token);
  // Backend returns user_id, map to id for frontend
  return {
    token: data.token,
    user: {
      id: data.user.user_id,
      email: data.user.email,
      name: data.user.name,
    },
  };
}

export async function authMe(): Promise<{
  id: string;
  email: string;
  name: string;
}> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_URL}/api/auth/me`, {
    method: "POST",
    headers,
  });
  if (!res.ok) {
    localStorage.removeItem("auth_token");
    throw new ApiError("Session expired", 401);
  }
  const data = await res.json();
  // Backend returns user_id, map to id
  return { id: data.user_id, email: data.email, name: data.name };
}

export function authLogout(): void {
  localStorage.removeItem("auth_token");
}

// ─── API response types ─────────────────────────────────────────

export interface ApiProfile {
  id: string;
  name: string;
  phase: Phase;
  consent_given_at: string | null;
}

export interface ApiGoal {
  id: string;
  user_id: string;
  title: string;
  description: string;
  frequency: string;
  target_per_week: number;
  status: "active" | "paused" | "completed";
  confirmed: boolean;
  milestones: ApiMilestone[];
  created_at: string;
}

export interface ApiMilestone {
  id: string;
  goal_id: string;
  title: string;
  week_number: number;
  completed: boolean;
  created_at: string;
}

export interface ApiConversationTurn {
  id: string;
  user_id: string;
  role: "user" | "assistant";
  content: string;
  phase: Phase;
  turn_number: number;
  tool_calls?: Record<string, unknown> | null;
  tool_results?: Record<string, unknown> | null;
  created_at: string;
}

export interface ApiConversationResponse {
  turns: ApiConversationTurn[];
  total: number;
}

// ─── API functions ──────────────────────────────────────────────

export async function fetchProfile(): Promise<ApiProfile> {
  const data = await apiFetch<{
    user_id: string;
    profile_id: string;
    display_name: string;
    phase: string;
    consent_given: boolean;
  }>("/api/profile");
  return {
    id: data.profile_id,
    name: data.display_name,
    phase: data.phase as Phase,
    consent_given_at: data.consent_given ? "true" : null,
  };
}

export async function fetchGoals(): Promise<ApiGoal[]> {
  // Backend wraps goals in { goals: [...] }
  const data = await apiFetch<{ goals: ApiGoal[] }>("/api/goals");
  return data.goals;
}

export async function fetchConversation(
  limit = 50,
  offset = 0
): Promise<ApiConversationResponse> {
  return apiFetch<ApiConversationResponse>(
    `/api/conversation?limit=${limit}&offset=${offset}`
  );
}

export async function grantConsent(
  version: string = "1.0"
): Promise<{ status: string; phase: string }> {
  // Backend expects consent_version, not version
  return apiFetch<{ status: string; phase: string }>("/api/consent", {
    method: "POST",
    body: JSON.stringify({ consent_version: version }),
  });
}

export async function sendChatSync(
  message: string
): Promise<{ response: string; phase?: Phase }> {
  return apiFetch<{ response: string; phase?: Phase }>("/api/chat/sync", {
    method: "POST",
    body: JSON.stringify({ message }),
  });
}

export async function streamChat(
  message: string,
  onEvent: (event: SSEEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const headers = getAuthHeaders();
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ message }),
    signal,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      body.detail ?? body.error ?? `Request failed with status ${res.status}`,
      res.status,
      body.code,
      body.detail
    );
  }

  const reader = res.body?.getReader();
  if (!reader) {
    throw new Error("No response body");
  }

  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events from buffer
      const lines = buffer.split("\n");
      buffer = lines.pop() ?? "";

      for (const line of lines) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith(":")) continue;
        if (trimmed.startsWith("data: ")) {
          const data = trimmed.slice(6);
          try {
            const event = JSON.parse(data) as SSEEvent;
            onEvent(event);
          } catch {
            // skip malformed JSON
          }
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
}

// ─── Adapters: convert API shapes to frontend types ─────────────

export function apiGoalToGoal(apiGoal: ApiGoal): Goal {
  return {
    id: apiGoal.id,
    title: apiGoal.title,
    status: apiGoal.status,
    confirmed: apiGoal.confirmed,
    milestones: (apiGoal.milestones ?? []).map((m) => ({
      title: m.title,
      week: m.week_number,
      completed: m.completed,
    })),
  };
}

export function apiTurnToMessage(turn: ApiConversationTurn): Message {
  // Handle tool_calls — backend stores as a single dict, not an array
  let toolCalls: Message["tool_calls"];
  if (turn.tool_calls && typeof turn.tool_calls === "object") {
    const tc = turn.tool_calls as Record<string, unknown>;
    if (tc.name) {
      toolCalls = [
        {
          tool: tc.name as string,
          args: (tc.args as Record<string, unknown>) ?? {},
          status: "complete" as const,
        },
      ];
    }
  }

  return {
    id: turn.id,
    role: turn.role,
    content: turn.content,
    phase: turn.phase,
    created_at: turn.created_at,
    tool_calls: toolCalls,
  };
}

export function computeAdherence(goals: Goal[]): AdherenceStats {
  const allMilestones = goals.flatMap((g) => g.milestones);
  const completedMilestones = allMilestones.filter((m) => m.completed);
  const completionRate =
    allMilestones.length > 0
      ? Math.round((completedMilestones.length / allMilestones.length) * 100)
      : 0;

  return {
    streak: 0,
    weeklyCompletion: completionRate,
    trend: "stable",
  };
}

// ─── Admin API functions ─────────────────────────────────────────

import type { DashboardPatient, DashboardAlert } from "@/lib/types";

export async function fetchAdminPatients(): Promise<DashboardPatient[]> {
  const data = await apiFetch<{ patients: DashboardPatient[] }>(
    "/api/admin/patients"
  );
  return data.patients;
}

export async function fetchAdminAlerts(): Promise<DashboardAlert[]> {
  const data = await apiFetch<{ alerts: DashboardAlert[] }>(
    "/api/admin/alerts"
  );
  return data.alerts;
}

export async function resetDemo(): Promise<{ status: string }> {
  return apiFetch<{ status: string }>("/api/admin/reset", { method: "POST" });
}
