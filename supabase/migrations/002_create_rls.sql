-- AI Health Coach: Row Level Security Policies
-- Migration 002: RLS on all tables

-- Enable RLS on all tables
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE goals ENABLE ROW LEVEL SECURITY;
ALTER TABLE milestones ENABLE ROW LEVEL SECURITY;
ALTER TABLE reminders ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_turns ENABLE ROW LEVEL SECURITY;
ALTER TABLE safety_audit_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversation_summaries ENABLE ROW LEVEL SECURITY;
ALTER TABLE clinician_alerts ENABLE ROW LEVEL SECURITY;

-- ============================================================
-- profiles: users can read/update their own profile
-- ============================================================
CREATE POLICY "profiles_select_own" ON profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "profiles_update_own" ON profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- ============================================================
-- goals: users can CRUD their own goals
-- ============================================================
CREATE POLICY "goals_select_own" ON goals
    FOR SELECT USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "goals_insert_own" ON goals
    FOR INSERT WITH CHECK (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "goals_update_own" ON goals
    FOR UPDATE USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- milestones: users can read/update their own (via denormalized user_id)
-- ============================================================
CREATE POLICY "milestones_select_own" ON milestones
    FOR SELECT USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

CREATE POLICY "milestones_update_own" ON milestones
    FOR UPDATE USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- reminders: users can read their own reminders
-- ============================================================
CREATE POLICY "reminders_select_own" ON reminders
    FOR SELECT USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- conversation_turns: users can read their own turns
-- ============================================================
CREATE POLICY "turns_select_own" ON conversation_turns
    FOR SELECT USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- conversation_summaries: users can read their own summaries
-- ============================================================
CREATE POLICY "summaries_select_own" ON conversation_summaries
    FOR SELECT USING (user_id IN (SELECT id FROM profiles WHERE user_id = auth.uid()));

-- ============================================================
-- safety_audit_log: service_role only (no user access)
-- ============================================================
-- No policies = no user access. service_role key bypasses RLS.

-- ============================================================
-- clinician_alerts: service_role only (no user access)
-- ============================================================
-- No policies = no user access. service_role key bypasses RLS.
