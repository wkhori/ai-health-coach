# Phase 0: Analysis — AI Health Coach

## 0.1 Requirements Extraction

| # | Requirement | Category | Explicit/Implied | Testable? |
|---|-------------|----------|------------------|-----------|
| 1 | Multi-turn onboarding conversation (welcome → reference exercises → elicit goal → extract structured goal → confirm → store) | AI / Conversation | Explicit | Yes — verify each step produces expected state transitions and stored goal |
| 2 | LangGraph agent with phase routing: PENDING → ONBOARDING → ACTIVE → RE_ENGAGING → DORMANT | AI / Architecture | Explicit | Yes — verify deterministic phase transitions via application code |
| 3 | Phase-specific subgraphs dispatched by main router graph | AI / Architecture | Explicit | Yes — verify each phase routes to correct subgraph |
| 4 | Safety classifier on every generated message before delivery | AI / Safety | Explicit | Yes — verify clinical content is blocked, safe content passes |
| 5 | Clinical boundary enforcement: hard redirect to care team for clinical content | AI / Safety | Explicit | Yes — test with clinical questions, verify redirect |
| 6 | Mental health crisis detection → urgent clinician alert | AI / Safety | Explicit | Yes — test with crisis signals, verify alert_clinician called with urgency |
| 7 | Blocked message retry with augmented prompt, then fallback to safe generic | AI / Safety | Explicit | Yes — verify retry logic and fallback path |
| 8 | Scheduled follow-up at Day 2, 5, 7 referencing patient's goal | Data / Scheduling | Explicit | Yes — verify scheduled messages are created and contain goal reference |
| 9 | Tone adjustment based on interaction type (celebration, nudge, check-in) | AI / UX | Explicit | Yes — verify prompt templates differ per interaction type |
| 10 | Exponential backoff on unanswered messages: 1 → 2 → 3 → dormant | Data / Logic | Explicit | Yes — verify message spacing and dormant transition after 3 |
| 11 | Clinician alert after 3 unanswered messages | Data / Safety | Explicit | Yes — verify alert_clinician called after 3rd unanswered |
| 12 | Warm re-engagement for dormant patients who return | AI / Conversation | Explicit | Yes — verify DORMANT → RE_ENGAGING transition and warm message |
| 13 | Tool calling: set_goal, set_reminder, get_program_summary, get_adherence_summary, alert_clinician | AI / Tools | Explicit | Yes — verify LLM invokes tools correctly with proper args |
| 14 | Tool implementations can be stubbed but interface and invocation logic must be real | AI / Tools | Explicit | Yes — verify tool schemas, invocation paths, and stub responses |
| 15 | Consent gate: no interaction without login + consent | Auth / Safety | Explicit | Yes — verify every interaction checks both conditions |
| 16 | Consent verified on every interaction, not just thread creation | Auth / Safety | Explicit | Yes — verify per-interaction check, not cached |
| 17 | Edge case: patient never responds | AI / Logic | Explicit | Yes — verify timeout → backoff → dormant flow |
| 18 | Edge case: unrealistic goals | AI / Conversation | Explicit | Yes — verify coach pushes back on unrealistic goals |
| 19 | Edge case: patient refuses to commit | AI / Conversation | Explicit | Yes — verify coach handles gracefully without forcing |
| 20 | Edge case: clinical questions mid-onboarding | AI / Safety | Explicit | Yes — verify safety classifier catches and redirects |
| 21 | Python required language | Infra | Explicit | Yes — project is Python |

## 0.2 Evaluation Criteria Mapping

No explicit rubric provided. Deriving from the brief's emphasis:

| Criterion | Priority | How to Prove It | Risk of Missing |
|-----------|----------|-----------------|-----------------|
| Correct phase routing (deterministic, not LLM-decided) | Critical | Unit tests for every phase transition path | Agent behaves unpredictably |
| Safety classifier blocks clinical content | Critical | Test suite with clinical/non-clinical messages | Patient gets clinical advice from AI |
| Mental health crisis detection | Critical | Test with crisis signals → verify urgent alert | Patient in crisis gets no help |
| Tool calling works correctly | High | Integration tests for each tool invocation | Agent can't perform core actions |
| Onboarding flow handles all edge cases | High | Conversation simulation tests | Onboarding breaks on edge cases |
| Scheduled follow-up logic | High | Unit tests for scheduling + tone selection | Patients don't get check-ins |
| Exponential backoff + dormant transition | High | State machine tests | Patients get spammed or ghost silently |
| Consent gate enforced on every interaction | Critical | Test that unconsented interactions are blocked | Legal/compliance violation |
| Code quality and test coverage | Medium | Passing test suite, type checking, linting | Maintenance burden, bugs |
| Demo-readiness | Medium | Seed data, realistic conversation logs | Can't demonstrate the system |

## 0.3 Gap Analysis

What the brief does NOT say that a production system needs:

- **Data persistence:** Brief implies storage (store goal, phase state) but doesn't specify. Need a database. → Supabase/PostgreSQL per preferences.
- **API layer:** How does the coach receive patient messages? Need an API. → FastAPI.
- **Message delivery:** Brief mentions "proactively engages" but no delivery channel specified. → Abstract message delivery interface (could be SMS, push, in-app).
- **Authentication:** Brief mentions "logged into MedBridge Go" but no auth implementation details. → Consent/auth check as middleware, not full auth system.
- **Conversation history:** Multi-turn conversation implies storage. → Thread/message storage in DB.
- **Observability/logging:** Not mentioned but critical for healthcare. → Structured logging.
- **Configuration:** Follow-up schedule (Day 2, 5, 7) should be configurable. → Config module.
- **Error handling:** What if Claude API fails mid-conversation? → Retry with fallback.
- **Rate limiting:** Patient could spam messages. → Basic rate limiting on API.
- **Testing harness:** Need to test LLM-dependent code. → Mock LLM responses in tests.
- **Seed data:** Need realistic patient/program data for demos.

## 0.4 Architecture Overview (Pre-Presearch)

This is a **Python backend system**, not a web app with UI. Key components:

```
┌─────────────────────────────────────────────┐
│                  FastAPI                      │
│  POST /chat    POST /webhook   GET /health   │
└──────────┬──────────────────────┬────────────┘
           │                      │
    ┌──────▼──────┐       ┌──────▼──────┐
    │ Consent Gate │       │  Scheduler   │
    └──────┬──────┘       └──────┬──────┘
           │                      │
    ┌──────▼──────────────────────▼──────┐
    │         LangGraph Router            │
    │  PENDING→ONBOARDING→ACTIVE→...     │
    └──────┬──────┬──────┬──────┬───────┘
           │      │      │      │
     ┌─────▼┐ ┌──▼──┐ ┌─▼───┐ ┌▼────────┐
     │Onboard│ │Active│ │Re-  │ │Dormant  │
     │Graph  │ │Graph │ │Engage│ │Graph    │
     └──┬───┘ └──┬──┘ └─┬───┘ └┬────────┘
        │        │      │      │
    ┌───▼────────▼──────▼──────▼───┐
    │       Safety Classifier       │
    │  (runs on EVERY outbound msg) │
    └───┬──────────────────────────┘
        │
    ┌───▼───────────────────────┐
    │        Tool Layer          │
    │ set_goal, set_reminder,   │
    │ get_program_summary,      │
    │ get_adherence_summary,    │
    │ alert_clinician           │
    └───┬───────────────────────┘
        │
    ┌───▼───────────────────────┐
    │    Database (Supabase)     │
    │ patients, threads, msgs,  │
    │ goals, reminders, alerts  │
    └───────────────────────────┘
```

## 0.5 File/Module Inventory

```
ai-health-coach/
├── src/
│   ├── __init__.py
│   ├── main.py                     # FastAPI app entry
│   ├── config.py                   # Settings, env vars
│   ├── models/
│   │   ├── __init__.py
│   │   ├── patient.py              # Patient, Consent, Thread models
│   │   ├── message.py              # Message model
│   │   ├── goal.py                 # Goal model
│   │   └── enums.py                # PhaseState, InteractionType enums
│   ├── db/
│   │   ├── __init__.py
│   │   ├── client.py               # Supabase client
│   │   ├── repositories.py         # Data access layer
│   │   └── seed.py                 # Seed data script
│   ├── graph/
│   │   ├── __init__.py
│   │   ├── router.py               # Main LangGraph router
│   │   ├── state.py                # Graph state definition
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── consent_check.py    # Consent gate node
│   │   │   ├── phase_router.py     # Deterministic phase dispatch
│   │   │   ├── safety_check.py     # Safety classifier node
│   │   │   └── message_delivery.py # Outbound message node
│   │   └── subgraphs/
│   │       ├── __init__.py
│   │       ├── onboarding.py       # ONBOARDING phase subgraph
│   │       ├── active.py           # ACTIVE phase subgraph
│   │       ├── re_engaging.py      # RE_ENGAGING phase subgraph
│   │       └── dormant.py          # DORMANT phase subgraph
│   ├── safety/
│   │   ├── __init__.py
│   │   ├── classifier.py           # Safety classification logic
│   │   └── prompts.py              # Safety check prompts
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── definitions.py          # Tool schemas for LLM
│   │   ├── set_goal.py             # set_goal implementation (stub)
│   │   ├── set_reminder.py         # set_reminder implementation (stub)
│   │   ├── get_program_summary.py  # get_program_summary (stub)
│   │   ├── get_adherence_summary.py# get_adherence_summary (stub)
│   │   └── alert_clinician.py      # alert_clinician implementation (stub)
│   ├── scheduler/
│   │   ├── __init__.py
│   │   └── follow_up.py            # Day 2/5/7 follow-up + backoff logic
│   └── prompts/
│       ├── __init__.py
│       ├── onboarding.py           # Onboarding conversation prompts
│       ├── active.py               # Active phase prompts
│       ├── re_engaging.py          # Re-engagement prompts
│       └── system.py               # System prompt (shared)
├── tests/
│   ├── __init__.py
│   ├── conftest.py                 # Shared fixtures, mock LLM
│   ├── test_consent_gate.py
│   ├── test_phase_routing.py
│   ├── test_safety_classifier.py
│   ├── test_onboarding_flow.py
│   ├── test_tool_calling.py
│   ├── test_scheduled_followup.py
│   ├── test_disengagement.py
│   ├── test_re_engagement.py
│   └── test_api.py
├── dev-docs/
├── pyproject.toml
├── CLAUDE.md
├── .env.example
├── .gitignore
└── README.md
```

This is the foundation. Presearch will refine architecture decisions.
