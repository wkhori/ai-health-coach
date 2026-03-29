-- AI Health Coach: Initial Schema
-- Migration 001: Create all tables

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ============================================================
-- profiles: user lifecycle + consent
-- ============================================================
CREATE TABLE profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    display_name TEXT NOT NULL DEFAULT '',
    timezone TEXT NOT NULL DEFAULT 'UTC',
    phase TEXT NOT NULL DEFAULT 'PENDING'
        CHECK (phase IN ('PENDING', 'ONBOARDING', 'ACTIVE', 'RE_ENGAGING', 'DORMANT')),
    phase_updated_at TIMESTAMPTZ,
    consent_given_at TIMESTAMPTZ,
    consent_revoked_at TIMESTAMPTZ,
    consent_version TEXT,
    onboarding_completed_at TIMESTAMPTZ,
    last_message_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(user_id)
);

CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_profiles_phase ON profiles(phase);

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- goals: patient exercise goals
-- ============================================================
CREATE TABLE goals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    frequency TEXT NOT NULL DEFAULT '',
    target_per_week INT NOT NULL DEFAULT 0,
    confirmed BOOLEAN NOT NULL DEFAULT false,
    status TEXT NOT NULL DEFAULT 'active'
        CHECK (status IN ('active', 'completed', 'paused', 'abandoned')),
    target_date DATE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(user_id, status);

CREATE TRIGGER goals_updated_at
    BEFORE UPDATE ON goals
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- milestones: weekly micro-milestones for goals
-- ============================================================
CREATE TABLE milestones (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    goal_id UUID NOT NULL REFERENCES goals(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    week_number INT NOT NULL,
    completed BOOLEAN NOT NULL DEFAULT false,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_milestones_goal ON milestones(goal_id, week_number);
CREATE INDEX idx_milestones_user ON milestones(user_id);

-- ============================================================
-- reminders: scheduled follow-ups + re-engagement messages
-- ============================================================
CREATE TABLE reminders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    reminder_type TEXT NOT NULL DEFAULT 'follow_up'
        CHECK (reminder_type IN ('follow_up', 'goal_check', 'custom')),
    message_template TEXT NOT NULL DEFAULT '',
    scheduled_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,
    sent_at TIMESTAMPTZ,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'sent', 'failed', 'cancelled')),
    retry_count INT NOT NULL DEFAULT 0,
    attempt_number INT NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_reminders_due ON reminders(status, due_at);
CREATE INDEX idx_reminders_user ON reminders(user_id);

-- ============================================================
-- conversation_turns: analytics/replay layer
-- ============================================================
CREATE TABLE conversation_turns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    phase TEXT NOT NULL,
    tool_calls JSONB,
    tool_results JSONB,
    token_count_input INT,
    token_count_output INT,
    turn_number INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_turns_user_time ON conversation_turns(user_id, created_at);
CREATE INDEX idx_turns_user_number ON conversation_turns(user_id, turn_number);

-- ============================================================
-- safety_audit_log: every safety classification decision
-- ============================================================
CREATE TABLE safety_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    conversation_turn_id UUID REFERENCES conversation_turns(id),
    input_text TEXT NOT NULL,
    classification TEXT NOT NULL
        CHECK (classification IN ('safe', 'clinical', 'crisis', 'ambiguous')),
    confidence FLOAT NOT NULL CHECK (confidence >= 0.0 AND confidence <= 1.0),
    categories JSONB NOT NULL DEFAULT '[]'::jsonb,
    flagged_phrases JSONB NOT NULL DEFAULT '[]'::jsonb,
    reasoning TEXT NOT NULL DEFAULT '',
    action_taken TEXT NOT NULL
        CHECK (action_taken IN ('passed', 'rewritten', 'blocked', 'escalated')),
    tier TEXT NOT NULL DEFAULT 'llm' CHECK (tier IN ('rule', 'llm')),
    model_used TEXT NOT NULL DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_safety_user ON safety_audit_log(user_id, created_at);
CREATE INDEX idx_safety_classification ON safety_audit_log(classification);

-- ============================================================
-- conversation_summaries: compressed conversation context
-- ============================================================
CREATE TABLE conversation_summaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    summary_text TEXT NOT NULL,
    turns_covered_from INT NOT NULL,
    turns_covered_to INT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_summaries_user ON conversation_summaries(user_id, created_at DESC);

-- ============================================================
-- clinician_alerts: escalation events
-- ============================================================
CREATE TABLE clinician_alerts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    safety_audit_id UUID REFERENCES safety_audit_log(id),
    alert_type TEXT NOT NULL
        CHECK (alert_type IN ('crisis', 'clinical_boundary', 'disengagement', 'repeated_flags')),
    urgency TEXT NOT NULL DEFAULT 'routine'
        CHECK (urgency IN ('routine', 'urgent')),
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'acknowledged', 'resolved')),
    message TEXT NOT NULL DEFAULT '',
    acknowledged_at TIMESTAMPTZ,
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_alerts_status ON clinician_alerts(status, created_at);
CREATE INDEX idx_alerts_user ON clinician_alerts(user_id);
