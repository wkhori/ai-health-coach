import type { DashboardAlert, DashboardPatient, Patient } from "./types";

/** Demo mode is active when no API URL is configured */
export const DEMO_MODE = !process.env.NEXT_PUBLIC_API_URL;

export const patients: Record<string, Patient> = {
  sarah: {
    id: "sarah-001",
    name: "Sarah Chen",
    phase: "ACTIVE",
    consentGiven: true,
    goals: [
      {
        id: "goal-s1",
        title: "Walk 30 minutes daily",
        status: "active",
        confirmed: true,
        milestones: [
          { title: "Walk 15 min 3x/week", week: 1, completed: true },
          { title: "Walk 20 min 4x/week", week: 2, completed: true },
          { title: "Walk 25 min 5x/week", week: 3, completed: true },
          { title: "Walk 30 min daily", week: 4, completed: false },
        ],
      },
      {
        id: "goal-s2",
        title: "Do stretching routine",
        status: "active",
        confirmed: true,
        milestones: [
          { title: "5 min morning stretch 3x/week", week: 1, completed: true },
          { title: "10 min stretch 4x/week", week: 2, completed: true },
          { title: "15 min stretch 5x/week", week: 3, completed: false },
          { title: "15 min stretch daily", week: 4, completed: false },
        ],
      },
    ],
    adherence: { streak: 12, weeklyCompletion: 85, trend: "up" },
    conversation: [
      {
        id: "msg-s1",
        role: "assistant",
        content:
          "Hi Sarah! Great to see you today. You've been on a 12-day streak with your walking goal \u2014 that's incredible consistency! How are you feeling about your progress this week?",
        phase: "ACTIVE",
        created_at: "2026-03-27T09:00:00Z",
      },
      {
        id: "msg-s2",
        role: "user",
        content:
          "Thanks! I've been really enjoying the morning walks. I'm thinking about trying to jog a bit too.",
        phase: "ACTIVE",
        created_at: "2026-03-27T09:01:00Z",
      },
      {
        id: "msg-s3",
        role: "assistant",
        content:
          "That's a wonderful progression! Your body has been building endurance over the past 12 days of consistent walking. Adding some light jogging intervals could be a great next step. Would you like me to set up a new goal for incorporating jogging, or would you prefer to adjust your current walking goal?",
        phase: "ACTIVE",
        created_at: "2026-03-27T09:02:00Z",
      },
    ],
  },
  marcus: {
    id: "marcus-001",
    name: "Marcus Johnson",
    phase: "ONBOARDING",
    consentGiven: true,
    goals: [],
    adherence: { streak: 0, weeklyCompletion: 0, trend: "stable" },
    conversation: [
      {
        id: "msg-m1",
        role: "assistant",
        content:
          "Welcome, Marcus! I'm your wellness coach, and I'm here to help you build healthy exercise habits that fit your life. Before we get started, I'd love to learn a bit about you. What kind of physical activities do you enjoy, or what have you tried in the past?",
        phase: "ONBOARDING",
        created_at: "2026-03-27T10:00:00Z",
      },
    ],
  },
  elena: {
    id: "elena-001",
    name: "Elena Rodriguez",
    phase: "RE_ENGAGING",
    consentGiven: true,
    goals: [
      {
        id: "goal-e1",
        title: "Swim laps 3x/week",
        status: "paused",
        confirmed: true,
        milestones: [
          { title: "Swim 10 laps 2x/week", week: 1, completed: true },
          { title: "Swim 15 laps 2x/week", week: 2, completed: true },
          { title: "Swim 15 laps 3x/week", week: 3, completed: false },
          { title: "Swim 20 laps 3x/week", week: 4, completed: false },
        ],
      },
      {
        id: "goal-e2",
        title: "Evening yoga routine",
        status: "paused",
        confirmed: true,
        milestones: [
          { title: "10 min yoga 2x/week", week: 1, completed: true },
          { title: "15 min yoga 3x/week", week: 2, completed: false },
          { title: "20 min yoga 3x/week", week: 3, completed: false },
          { title: "20 min yoga 4x/week", week: 4, completed: false },
        ],
      },
    ],
    adherence: { streak: 0, weeklyCompletion: 30, trend: "down" },
    conversation: [
      {
        id: "msg-e1",
        role: "assistant",
        content:
          "Hi Elena! It's been a little while since we last chatted. I hope you've been doing well. I noticed your swimming and yoga routines have been paused. Life gets busy sometimes, and that's completely okay. Would you like to talk about what's been going on, or should we look at adjusting your goals to fit your current schedule?",
        phase: "RE_ENGAGING",
        created_at: "2026-03-27T11:00:00Z",
      },
    ],
  },
};

export const patientIds = Object.keys(patients) as Array<keyof typeof patients>;

// ─── Dashboard demo data ─────────────────────────────────────────

export const dashboardPatients: DashboardPatient[] = [
  {
    user_id: "sarah-001",
    profile_id: "sarah-profile-001",
    display_name: "Sarah Chen",
    phase: "ACTIVE",
    last_message_at: "2026-03-29T09:02:00Z",
    active_goals_count: 2,
    total_milestones: 8,
    completed_milestones: 5,
    adherence_pct: 85,
    alerts_count: 0,
  },
  {
    user_id: "marcus-001",
    profile_id: "marcus-profile-001",
    display_name: "Marcus Johnson",
    phase: "ONBOARDING",
    last_message_at: "2026-03-29T06:30:00Z",
    active_goals_count: 0,
    total_milestones: 0,
    completed_milestones: 0,
    adherence_pct: 0,
    alerts_count: 0,
  },
  {
    user_id: "elena-001",
    profile_id: "elena-profile-001",
    display_name: "Elena Rodriguez",
    phase: "RE_ENGAGING",
    last_message_at: "2026-03-24T14:00:00Z",
    active_goals_count: 0,
    total_milestones: 8,
    completed_milestones: 3,
    adherence_pct: 25,
    alerts_count: 1,
  },
];

export const dashboardAlerts: DashboardAlert[] = [
  {
    id: "alert-001",
    user_id: "elena-001",
    patient_name: "Elena Rodriguez",
    alert_type: "disengagement",
    urgency: "routine",
    message:
      "Patient has not responded for 5 days. Re-engagement attempt 1 of 3 sent.",
    created_at: "2026-03-24T10:00:00Z",
  },
];
