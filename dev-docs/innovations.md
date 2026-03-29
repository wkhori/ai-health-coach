# Phase 1: Innovations — AI Health Coach

## Proposed Innovations

### 1. Conversation Sentiment Tracking & Adaptive Tone Engine
**Category:** Novel AI Application
**What:** Track patient sentiment across conversations using Claude's analysis capabilities, building a per-patient "emotional trajectory" that informs tone selection (not just interaction-type-based, but patient-mood-aware).
**Why differentiating:** The brief asks for tone adjustment by interaction type (celebration/nudge/check-in). This goes further — same check-in could be warm and encouraging for a patient trending positive, or gentle and empathetic for one trending down. Turns a static tone selector into a dynamic emotional intelligence layer.
**Effort:** Medium
**Assigned to Phase:** Phase 4 (Active Phase Subgraph)

### 2. Goal Decomposition & Micro-Milestone Tracking
**Category:** Domain Intelligence
**What:** When a patient sets a goal like "do my exercises 5 times a week," the coach automatically decomposes it into daily micro-milestones and celebrates each one. Creates a "streak" mental model that leverages behavioral psychology (small wins compound).
**Why differentiating:** The brief stores one structured goal. This creates a progression system that gives the coach something specific to reference in every follow-up ("You've hit 3 of your 5 sessions this week — amazing!"), making conversations feel personalized rather than generic.
**Effort:** Medium
**Assigned to Phase:** Phase 3 (Tool Layer — extends set_goal + get_adherence_summary)

### 3. Proactive Insight Generation from Adherence Patterns
**Category:** Data-Driven Optimization
**What:** Analyze adherence patterns to generate insights: "You tend to exercise more on weekday mornings — want me to schedule your reminders for 8am?" or "You've been consistent for 2 weeks straight — that's when most patients see real results."
**Why differentiating:** Most health apps show data. This coach interprets patterns and offers actionable suggestions, making the AI feel like it actually understands the patient's behavior rather than just nagging on a schedule.
**Effort:** Medium
**Assigned to Phase:** Phase 4 (Active Phase Subgraph — after Day 7)

### 4. Graduated Re-Engagement with Context Memory
**Category:** UX Excellence
**What:** When a dormant patient returns, instead of a generic "Welcome back!", the coach references their last known state: "Hey! Last time we talked, you were crushing your 3x/week goal. Want to pick up where we left off, or set a new target?" Includes a "no guilt" framing to reduce shame-based avoidance.
**Why differentiating:** The brief mentions "warm re-engagement" but doesn't specify what that means. This makes re-engagement feel human — it remembers, doesn't judge, and offers a path forward. Critical for the actual health outcome (getting patients back on track).
**Effort:** Low
**Assigned to Phase:** Phase 5 (Re-Engagement Subgraph)

### 5. Safety Classifier Confidence Scoring with Audit Trail
**Category:** Production Hardening
**What:** Instead of binary safe/unsafe, the safety classifier outputs a confidence score (0-1). Messages scoring 0.3-0.7 get human review queued (not blocked). Full audit trail of every classification decision stored for compliance review. Includes weekly safety report generation.
**Why differentiating:** Healthcare compliance requires auditability. A binary classifier either over-blocks (frustrating patients) or under-blocks (liability risk). Confidence scoring with a review queue handles the gray zone that real clinical conversations inevitably hit.
**Effort:** Medium
**Assigned to Phase:** Phase 2 (Safety Classifier)

### 6. Conversation Replay & Clinician Dashboard Data Model
**Category:** Demo-Ready Polish
**What:** Store conversations in a structured format that could power a clinician dashboard (not building the dashboard — but the data model and API endpoints that would feed one). Include a CLI command that replays a patient's full conversation history with timestamps and phase transitions for demo purposes.
**Why differentiating:** Makes the demo compelling — you can show the full patient journey (onboard → goal set → follow-ups → re-engagement) as a timeline. Also shows production thinking (clinicians need visibility into AI interactions with their patients).
**Effort:** Low
**Assigned to Phase:** Phase 6 (API Layer + Demo Tooling)
