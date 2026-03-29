# AI Health Coach

An AI-powered accountability partner for home exercise program (HEP) adherence. Built as a wellness coaching agent that helps patients stick to their prescribed exercise routines through goal-setting, progress tracking, and context-aware re-engagement.

## Architecture

```
                          AI Health Coach — System Architecture
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                              FastAPI Server                                 │
 │  POST /api/chat (SSE)  POST /api/consent  GET /api/profile  GET /api/goals │
 │  POST /api/chat/sync   GET /api/health    GET /api/conversation            │
 │  GET /api/admin/patients  GET /api/admin/alerts  POST /api/admin/reset     │
 └──────────────────────────────────┬──────────────────────────────────────────┘
                                    │
                                    ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                          LangGraph Main Graph                               │
 │                                                                             │
 │  START ──► load_context ──► consent_gate ──► phase_router ──► [subgraph]   │
 │                                                                    │        │
 │            ┌─────────────────┬──────────────────┐                  │        │
 │            │   ONBOARDING    │     ACTIVE        │  RE_ENGAGING    │        │
 │            │   (set_goal)    │ (set_goal,        │  (set_goal,     │        │
 │            │                 │  set_reminder,    │   get_program)  │        │
 │            │                 │  get_program,     │                 │        │
 │            │                 │  get_adherence,   │                 │        │
 │            │                 │  alert_clinician) │                 │        │
 │            └────────┬────────┴────────┬─────────┘                  │        │
 │                     └────────┬────────┘                            │        │
 │                              ▼                                              │
 │                       safety_classifier                                     │
 │                     (Tier 1: Rules + Tier 2: LLM)                          │
 │                              │                                              │
 │                    ┌─────────┼─────────┬──────────┐                        │
 │                    ▼         ▼         ▼          ▼                         │
 │                  PASS    REWRITE    BLOCK     ESCALATE                      │
 │                    └─────────┴─────────┴──────────┘                        │
 │                              │                                              │
 │                     log_and_respond ──► check_phase_transition ──► END     │
 └──────────────────────────────┬──────────────────────────────────────────────┘
                                │
                                ▼
 ┌─────────────────────────────────────────────────────────────────────────────┐
 │                            SQLite Database                                  │
 │   profiles │ goals │ milestones │ reminders │ conversation_turns           │
 │   safety_audit_log │ conversation_summaries │ clinician_alerts             │
 └─────────────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.12+ |
| LLM | Claude Haiku 4.5 via `langchain_anthropic` |
| Agent Framework | LangGraph |
| Database | SQLite |
| API | FastAPI + SSE (sse-starlette) |
| Auth | Session-based token auth |
| Frontend | Next.js 16, React 19, Tailwind CSS v4, shadcn/ui |
| Testing | pytest + pytest-asyncio (700+ tests) |
| Linting | ruff |
| Logging | structlog |

## Features

- **Clinician Dashboard** — Multi-patient triage view with phase distribution, safety alerts, adherence tracking
- **4-Week Milestone Timeline** — Visual journey map showing patient progress through goal milestones
- **Live Demo Controls** — Real-time panel showing safety classifications, tool calls, and phase state
- **SSE Streaming Chat** — Token-by-token streaming with tool call visualization
- **Two-Tier Safety System** — Regex pre-filter + LLM classifier on every outbound message
- **Phase-Based Routing** — Deterministic state machine (PENDING → ONBOARDING → ACTIVE → RE_ENGAGING → DORMANT)
- **Consent Gate** — Verified on every interaction before any coaching occurs
- **Demo Mode** — Fully functional offline demo with hardcoded patient data

## Setup

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- An Anthropic API key (for real mode; demo mode works without it)

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd ai-health-coach

# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Copy environment template
cp .env.example .env
# Edit .env with your keys
```

### Environment Variables

```bash
# Required (for real mode)
ANTHROPIC_API_KEY=sk-ant-...

# Optional
DATABASE_PATH=health_coach.db          # SQLite path (default: health_coach.db)
LOG_LEVEL=INFO                         # Logging level
CORS_ORIGINS=http://localhost:3000     # Allowed CORS origins

# Optional (LangSmith observability)
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=lsv2_...
LANGCHAIN_PROJECT=ai-health-coach
```

### Frontend

```bash
cd web
npm install
npm run dev    # Start dev server on :3000
npm run build  # Production build
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` to connect to the backend. Without it, the frontend runs in demo mode with hardcoded data.

### Seed Data

```bash
# Seed the database with 3 demo patients
python -m src.db.seed

# Start the API server
uvicorn src.main:app --reload --port 8000
```

Demo patients:
- **Sarah Chen** (ACTIVE) — 2 confirmed goals, 12-day streak, 85% adherence
- **Marcus Johnson** (ONBOARDING) — 1 unconfirmed goal, new patient
- **Elena Rodriguez** (RE_ENGAGING) — 2 paused goals, 5 days inactive

## API Documentation

### Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/health` | No | Health check |
| `POST` | `/api/chat` | JWT | SSE streaming chat |
| `POST` | `/api/chat/sync` | JWT | Non-streaming chat fallback |
| `POST` | `/api/consent` | JWT | Grant consent |
| `GET` | `/api/profile` | JWT | Get user profile + phase |
| `GET` | `/api/goals` | JWT | Get user goals + milestones |
| `GET` | `/api/conversation` | JWT | Paginated conversation history |
| `GET` | `/api/admin/patients` | No | All patients with stats (demo) |
| `GET` | `/api/admin/alerts` | No | Unacknowledged clinician alerts |
| `POST` | `/api/admin/reset` | No | Re-seed database |

### SSE Event Types

```
token          — Streamed token from LLM response
tool_start     — Tool execution starting
tool_end       — Tool execution completed
phase_change   — Patient phase transition
safety_result  — Safety classification result
done           — Response complete
error          — Error occurred
```

### Rate Limiting

- 10 messages per minute per user (sliding window)
- Returns `429 Too Many Requests` with `Retry-After: 60` header

## Patient Lifecycle

```
PENDING ──[consent]──► ONBOARDING ──[goal confirmed]──► ACTIVE
                                                            │
                                                    [48h inactivity]
                                                            ▼
                                                      RE_ENGAGING
                                                       │        │
                                                [user msg]  [3 attempts]
                                                       │        │
                                                       ▼        ▼
                                                     ACTIVE   DORMANT
                                                                │
                                                          [user msg]
                                                                │
                                                                ▼
                                                          RE_ENGAGING
```

### Phase Details

- **PENDING**: Awaiting consent. No subgraph, no tools.
- **ONBOARDING**: Goal-setting phase. Tool: `set_goal`.
- **ACTIVE**: Main coaching loop. Tools: `set_goal`, `set_reminder`, `get_program_summary`, `get_adherence_summary`, `alert_clinician`.
- **RE_ENGAGING**: Backoff schedule (Day 2, 5, 7). Tools: `set_goal`, `get_program_summary`.
- **DORMANT**: After 3 failed re-engagement attempts. No tools. Any user message reactivates.

## Safety System

Two-tier safety classifier runs on every outbound message:

- **Tier 1 (Rules)**: Regex-based fast pass/block for crisis keywords, dosage patterns, diagnostic language, and positive reinforcement.
- **Tier 2 (LLM)**: Claude Haiku classifier for ambiguous cases with structured output.

Decision thresholds:
- Safe + confidence >= 0.8 -> PASS
- Crisis (any confidence) -> BLOCK + urgent clinician alert
- Clinical + confidence >= 0.6 -> REWRITE
- Low confidence -> BLOCK (err on caution)

Crisis responses are hard-coded strings (never LLM-generated) that include the 988 Suicide & Crisis Lifeline and Crisis Text Line numbers.

## Testing

```bash
# Run all tests (700+)
pytest tests/

# Run with verbose output
pytest tests/ -v

# Run specific test file
pytest tests/test_safety.py

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing

# Stop on first failure
pytest tests/ -x
```

### Test Structure

```
tests/
  conftest.py                 # Shared fixtures, mock LLM, mock DB
  test_safety.py              # Safety classifier (Tier 1 + Tier 2 + thresholds)
  test_adversarial.py         # 100+ adversarial prompts (parametrized)
  test_edge_cases.py          # 4 brief edge cases + extras
  test_error_recovery.py      # Error handling (LLM/DB/tool failures)
  test_journey.py             # Full patient journey E2E
  test_tools.py               # Tool implementations + phase binding
  test_state.py               # Graph state schema
  test_consent.py             # Consent gate
  test_routing.py             # Phase routing (deterministic)
  test_onboarding.py          # Onboarding subgraph
  test_active.py              # Active subgraph
  test_re_engage.py           # Re-engagement subgraph
  test_safety_node.py         # Safety node in graph context
  test_summarize.py           # Summarization logic
  test_api.py                 # FastAPI endpoints + admin endpoints
  test_repositories.py        # Database repository tests
  test_scheduling.py          # Scheduling logic
  adversarial_prompts.json    # Adversarial prompt bank (100+ prompts)
```

## Development

```bash
# Start dev server
uvicorn src.main:app --reload --port 8000

# Lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check src/ tests/ --fix

# Format code
ruff format src/ tests/

# Type check
pyright src/
```

## Key Constraints

| Constraint | Value |
|-----------|-------|
| Safety FN rate | < 1% |
| Safety FP rate | < 10% |
| TTFT target | < 1s |
| p95 response time | < 3s |
| Rate limit | 10 msg/min/user |
| Summarization interval | Every 6 turns |
| Re-engage schedule | Day 2, 5, 7 |
| Max re-engage attempts | 3 |
| Inactivity threshold | 48 hours |
