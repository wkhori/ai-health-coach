# AI Health Coach — Complete Upgrade Plan

> Full specification for closing all backend gaps, wiring the frontend to the real API, and making the project demo-ready.

---

## Table of Contents

1. [Current State Assessment](#1-current-state-assessment)
2. [Phase 1: Tool Binding & Execution Loop](#2-phase-1-tool-binding--execution-loop)
3. [Phase 2: Checkpointer Integration](#3-phase-2-checkpointer-integration)
4. [Phase 3: Repository Wiring](#4-phase-3-repository-wiring)
5. [Phase 4: Summarization Node](#5-phase-4-summarization-node)
6. [Phase 5: Safety Retry Logic](#6-phase-5-safety-retry-logic)
7. [Phase 6: SSE Streaming Completion](#7-phase-6-sse-streaming-completion)
8. [Phase 7: LLM Wiring in Main App](#8-phase-7-llm-wiring-in-main-app)
9. [Phase 8: Missing Test Files](#9-phase-8-missing-test-files)
10. [Phase 9: Frontend Upgrade & Integration](#10-phase-9-frontend-upgrade--integration)
11. [Dependency Order & Execution Strategy](#11-dependency-order--execution-strategy)

---

## 1. Current State Assessment

### What Works

| Component | Status | Evidence |
|---|---|---|
| Graph flow (14 nodes, conditional edges) | Complete | `src/graph/router.py` — correct START->END path |
| Deterministic phase routing | Complete | `src/graph/nodes/phase_router.py` — dict lookup, no LLM |
| All 6 phase transitions | Complete | `src/graph/nodes/phase_transition.py:15-21` |
| Safety classifier (Tier 1 + Tier 2) | Complete | `src/safety/rules.py` + `src/safety/classifier.py` |
| Hard-coded crisis responses with 988 hotline | Complete | `src/graph/nodes/message_delivery.py:14-21` |
| Prompt injection defense (3 layers) | Complete | `src/safety/sanitizer.py` + `src/prompts/system.py` |
| Consent gate (verified every interaction) | Complete | `src/graph/nodes/consent_check.py` |
| 8-table DB schema + RLS | Complete | `supabase/migrations/001_*.sql` + `002_*.sql` |
| 8 repository classes | Complete | `src/db/repositories.py` |
| 5 tool definitions (`@tool` decorated) | Complete | `src/tools/definitions.py` |
| All 7 API endpoints + webhook | Complete | `src/main.py:183-456` |
| Rate limiting (10 msg/min sliding window) | Complete | `src/main.py:44-152` |
| SSE streaming (token/tool_start/tool_end/done/error) | Partial | Missing `phase_change` event |
| Test suite (290 tests, 113 adversarial prompts) | Mostly Complete | Missing 4 spec'd test files |
| Frontend UI shell (chat, sidebar, phase badges) | Complete | All components built in `web/components/` |
| Pydantic models + enums | Complete | `src/models/` |
| Configuration | Complete | `src/config.py` |

### What's Broken (7 Critical Gaps)

| Gap | Severity | Impact | Root Cause |
|---|---|---|---|
| **Tools never bound or executed** | CRITICAL | LLM cannot call any tools — core coaching loop broken | `.bind_tools()` never called; `ToolNode` never used |
| **No LLM instantiated in app** | CRITICAL | Subgraphs always hit fallback branch (`if not llm:`) | No `ChatAnthropic` created and passed to subgraphs |
| **Checkpointer not integrated** | HIGH | No cross-turn persistence — every request starts fresh | `AsyncPostgresSaver` never imported/instantiated |
| **Repositories never initialized** | HIGH | All DB-dependent endpoints return 503 | `get_repos()` has `pass` in body |
| **Summarization not wired** | MEDIUM | Conversations never summarized, context grows unbounded | Node exists but not in graph |
| **No blocked message retry** | MEDIUM | Blocked messages return static response immediately | No retry-with-augmented-prompt logic |
| **Frontend 100% mocked** | HIGH | Zero API calls — all responses from hardcoded scripts | No `fetch()`, no `EventSource`, no auth |

---

## 2. Phase 1: Tool Binding & Execution Loop

### Problem

The 5 tools (`set_goal`, `set_reminder`, `get_program_summary`, `get_adherence_summary`, `alert_clinician`) are defined in `src/tools/definitions.py` with `@tool` decorators, but:

1. **`.bind_tools()` is never called** — The subgraphs call `llm.ainvoke(messages)` at `onboarding.py:39`, `active.py:53`, `re_engaging.py:74` without binding tools, so the LLM never knows tools exist.

2. **`ToolNode` is never imported or used** — The `should_continue_*()` functions (`onboarding.py:63-75`, `active.py:62-72`, `re_engaging.py:83-93`) check for tool calls but nothing executes them.

3. **Subgraphs are async functions, not compiled StateGraphs** — Per CLAUDE.md: "Subgraphs are compiled StateGraphs added to the main graph via `add_node()`." Currently they are plain async functions that do a single LLM call.

### Spec

#### 2.1 Convert Each Subgraph to a Compiled StateGraph

Each subgraph must become a `StateGraph` with an agent-tool loop:

```
agent_node (LLM with bound tools)
    ↓
should_continue (conditional edge)
    ├── "tools" → tool_node (ToolNode)
    │                 ↓
    │              agent_node (loop back)
    └── "done" → END
```

#### 2.2 Onboarding Subgraph (`src/graph/subgraphs/onboarding.py`)

**Tools to bind:** `[set_goal]`

Changes required:
- Import `ToolNode` from `langgraph.prebuilt`
- Import `set_goal` from `src.tools.definitions`
- Import `StateGraph`, `END` from `langgraph.graph`
- Create a `build_onboarding_subgraph(llm)` function that:
  1. Binds tools: `bound_llm = llm.bind_tools([set_goal])`
  2. Creates an `agent_node` that invokes `bound_llm` with system prompt + messages
  3. Creates a `ToolNode([set_goal])` as `tool_node`
  4. Adds conditional edge from `agent_node` using `should_continue_onboarding`:
     - `"tools"` → `tool_node`
     - `"done"` → `END`
  5. Adds edge from `tool_node` back to `agent_node`
  6. Compiles and returns the subgraph
- Keep the existing `onboard_agent()` fallback for when `llm=None`
- Keep `check_onboarding_complete()` as-is (used by phase transition node)

#### 2.3 Active Subgraph (`src/graph/subgraphs/active.py`)

**Tools to bind:** `[set_goal, set_reminder, get_program_summary, get_adherence_summary, alert_clinician]`

Same pattern as onboarding:
- `build_active_subgraph(llm)` that binds all 5 tools
- Agent-tool loop with `should_continue_active`
- Include context formatting (`_format_goals`, `_format_adherence`, `_format_milestones`) in the agent node

#### 2.4 Re-Engaging Subgraph (`src/graph/subgraphs/re_engaging.py`)

**Tools to bind:** `[set_goal, get_program_summary]` (per CLAUDE.md spec)

Same pattern:
- `build_re_engaging_subgraph(llm)` that binds 2 tools
- Agent-tool loop with `should_continue_re_engage`
- Include context building (`build_re_engage_context`) in the agent node

#### 2.5 Update Router (`src/graph/router.py`)

Modify `build_graph()` to accept an `llm` parameter and pass compiled subgraphs as nodes:

```python
def build_graph(*, llm=None, checkpointer=None, ...):
    # Build subgraph instances
    if llm:
        onboarding_sg = build_onboarding_subgraph(llm)
        active_sg = build_active_subgraph(llm)
        re_engaging_sg = build_re_engaging_subgraph(llm)
    else:
        # Fallback to simple async functions for tests
        onboarding_sg = onboarding_fn or _default_onboarding
        active_sg = active_fn or _default_active
        re_engaging_sg = re_engaging_fn or _default_re_engaging

    graph.add_node("onboarding_subgraph", onboarding_sg)
    graph.add_node("active_subgraph", active_sg)
    graph.add_node("re_engaging_subgraph", re_engaging_sg)
```

#### 2.6 Fix Tool User ID

The tools currently use a hardcoded `_CURRENT_USER_ID` at `definitions.py:19`. This must be set from graph state before tool execution. Options:

- **Option A (recommended):** Pass `user_id` into tool context via LangGraph's `config` mechanism. Modify each tool's `_get_*_repo()` pattern to accept user_id as a parameter.
- **Option B:** Set the module-level `_CURRENT_USER_ID` at the beginning of each subgraph agent node before invoking the LLM. This is the current design — just needs the assignment wired.

### Files to Modify

| File | Changes |
|---|---|
| `src/graph/subgraphs/onboarding.py` | Rewrite as compiled StateGraph with tool loop |
| `src/graph/subgraphs/active.py` | Rewrite as compiled StateGraph with tool loop |
| `src/graph/subgraphs/re_engaging.py` | Rewrite as compiled StateGraph with tool loop |
| `src/graph/router.py` | Accept `llm` param, use compiled subgraphs |
| `src/tools/definitions.py` | Fix `_CURRENT_USER_ID` injection |

### Tests to Update

- `tests/test_onboarding.py` — Test with mock LLM that returns tool calls
- `tests/test_active.py` — Test all 5 tools are bound and callable
- `tests/test_re_engage.py` — Test 2 tools are bound
- `tests/test_tools.py` — Test tool execution through ToolNode
- `tests/test_routing.py` — Verify subgraphs are wired correctly

---

## 3. Phase 2: Checkpointer Integration

### Problem

`AsyncPostgresSaver` from `langgraph-checkpoint-postgres` is specified in CLAUDE.md (D22) but never imported or instantiated anywhere in `src/`. The graph is compiled without a checkpointer (`src/main.py:167`), so every request starts with a blank state — no conversation continuity.

### Spec

#### 3.1 Add Checkpointer to App Lifespan

**File:** `src/main.py`

In the `lifespan()` function (lines 23-39), after getting settings:

1. Import `AsyncPostgresSaver` from `langgraph.checkpoint.postgres.aio`
2. Create instance with `settings.supabase_db_url` (direct connection, port 5432)
3. Call `await checkpointer.asetup()` to auto-create checkpoint tables
4. Store as module-level `_checkpointer`
5. On shutdown, close the connection

#### 3.2 Pass Checkpointer to Graph

**File:** `src/main.py`

Modify `get_graph()` (lines 161-168):
- Pass `_checkpointer` to `build_graph(checkpointer=_checkpointer)`

The graph already accepts and uses checkpointer at `router.py:129`: `graph.compile(checkpointer=checkpointer)`.

#### 3.3 Thread ID Strategy

Already correct: `config = {"configurable": {"thread_id": user_id}}` at `main.py:220,295,447`.

Per CLAUDE.md: "Thread ID = patient's profile ID for conversation continuity." Consider switching from `user_id` to `profile_id` once profiles are loaded. For now, `user_id` works since each user has one profile.

#### 3.4 Dependency

Verify `langgraph-checkpoint-postgres` is in `pyproject.toml`. If not, add `langgraph-checkpoint-postgres>=2.0.0`.

### Files to Modify

| File | Changes |
|---|---|
| `src/main.py` | Import AsyncPostgresSaver, init in lifespan, pass to build_graph |
| `pyproject.toml` | Verify/add `langgraph-checkpoint-postgres>=2.0.0` + `asyncpg` |

---

## 4. Phase 3: Repository Wiring

### Problem

`get_repos()` at `src/main.py:171-177` is completely stubbed out — the body is `pass`, returning an empty dict. Every endpoint that calls `get_repos()` will get empty repos and either return 503 or silently skip DB operations.

Meanwhile, graph nodes (`load_context`, `log_and_respond`, `check_phase_transition`, `run_safety_check`) accept repos as keyword-only params that default to `None`, causing them to skip all DB operations.

### Spec

#### 4.1 Initialize Repositories in `get_repos()`

**File:** `src/main.py`

Replace the stubbed `get_repos()` with:

```python
def get_repos(settings: Settings | None = None) -> dict[str, Any]:
    global _repos
    if not _repos:
        if settings is None:
            settings = get_settings()
        from src.db.client import get_admin_client
        from src.db.repositories import (
            ProfileRepository, GoalRepository, MilestoneRepository,
            ReminderRepository, ConversationRepository,
            SafetyAuditRepository, SummaryRepository, AlertRepository,
        )
        client = get_admin_client(settings)
        _repos = {
            "profile": ProfileRepository(client),
            "goal": GoalRepository(client),
            "milestone": MilestoneRepository(client),
            "reminder": ReminderRepository(client),
            "conversation": ConversationRepository(client),
            "safety_audit": SafetyAuditRepository(client),
            "summary": SummaryRepository(client),
            "alert": AlertRepository(client),
        }
    return _repos
```

#### 4.2 Inject Repos into Graph Nodes

**File:** `src/graph/router.py`

The problem: `build_graph()` adds nodes like `graph.add_node("load_context", load_context)` but `load_context()` requires repos as keyword args. Since LangGraph calls node functions with `(state)` only, the repos never arrive.

Solution: Use `functools.partial` to pre-bind repos to node functions.

Add a `repos` parameter to `build_graph()`:

```python
def build_graph(*, llm=None, checkpointer=None, repos=None, ...):
    from functools import partial

    repos = repos or {}
    profile_repo = repos.get("profile")
    goal_repo = repos.get("goal")
    summary_repo = repos.get("summary")
    conversation_repo = repos.get("conversation")
    safety_audit_repo = repos.get("safety_audit")

    graph.add_node("load_context", partial(
        load_context_fn or load_context,
        profile_repo=profile_repo,
        goal_repo=goal_repo,
        summary_repo=summary_repo,
        conversation_repo=conversation_repo,
    ))
    graph.add_node("log_and_respond", partial(
        log_and_respond_fn or log_and_respond,
        conversation_repo=conversation_repo,
    ))
    graph.add_node("check_phase_transition", partial(
        check_phase_transition_fn or check_phase_transition,
        profile_repo=profile_repo,
    ))
```

#### 4.3 Wire Safety Classifier with Repos

The `run_safety_check` node accepts `safety_classifier` as a kwarg. Create a default classifier that chains Tier 1 + Tier 2 + audit logging:

```python
def _build_default_safety_classifier(safety_audit_repo=None):
    def classify(text):
        from src.safety.rules import tier1_classify
        from src.safety.classifier import tier2_classify, decide_action

        result = tier1_classify(text)
        tier = "tier1"
        if result is None:
            result = tier2_classify(text)
            tier = "tier2"

        action = decide_action(result)

        # Log to audit
        if safety_audit_repo:
            safety_audit_repo.log_entry(...)

        return {
            "classification": result.classification,
            "confidence": result.confidence,
            "categories": result.categories,
            "action": action.value,
            "reasoning": result.reasoning,
        }
    return classify
```

Bind it in `build_graph()`:

```python
classifier = _build_default_safety_classifier(safety_audit_repo)
graph.add_node("safety_check", partial(
    safety_check_fn or run_safety_check,
    safety_classifier=classifier,
))
```

#### 4.4 Update `get_graph()` in `main.py`

```python
def get_graph() -> Any:
    global _graph_instance
    if _graph_instance is None:
        from src.graph.router import build_graph
        repos = get_repos()
        _graph_instance = build_graph(
            llm=_llm_instance,
            checkpointer=_checkpointer,
            repos=repos,
        )
    return _graph_instance
```

#### 4.5 Fix `get_admin_client` Signature

Check `src/db/client.py` — `get_admin_client()` currently takes no args or accepts `settings`. Ensure it works with the settings instance passed from `get_repos()`.

### Files to Modify

| File | Changes |
|---|---|
| `src/main.py` | Implement `get_repos()`, update `get_graph()` |
| `src/graph/router.py` | Accept `repos` param, use `functools.partial` for node injection |
| `src/db/client.py` | Verify `get_admin_client(settings)` works |

---

## 5. Phase 4: Summarization Node

### Problem

`summarize_conversation()` is fully implemented in `src/graph/nodes/summarize.py` (lines 26-80) with LLM invocation, DB persistence, and turn-count gating. But it is **never wired into the graph** — `src/graph/router.py` has no reference to it.

### Spec

#### 5.1 Add Summarization as Conditional Step

**File:** `src/graph/router.py`

Insert the summarization node between `log_and_respond` and `check_phase_transition`:

1. Import `summarize_conversation` and `should_summarize` from `src.graph.nodes.summarize`
2. Add node: `graph.add_node("summarize", partial(summarize_conversation, llm=llm, summary_repo=summary_repo))`
3. Replace the direct edge at line 126:

**Current:**
```python
graph.add_edge("log_and_respond", "check_phase_transition")
```

**Replace with:**
```python
def _should_summarize_router(state):
    if should_summarize(state, every_n=6):
        return "summarize"
    return "skip"

graph.add_conditional_edges(
    "log_and_respond",
    _should_summarize_router,
    {
        "summarize": "summarize",
        "skip": "check_phase_transition",
    },
)
graph.add_edge("summarize", "check_phase_transition")
```

#### 5.2 Updated Graph Flow

```
... -> log_and_respond -> [should_summarize?]
                              ├── yes -> summarize -> check_phase_transition -> END
                              └── no  -> check_phase_transition -> END
```

### Files to Modify

| File | Changes |
|---|---|
| `src/graph/router.py` | Import summarize, add node, add conditional edge |

---

## 6. Phase 5: Safety Retry Logic

### Problem

Per the requirements: "Blocked messages retry once with an augmented prompt, then fall back to a safe generic message." Currently, `output_blocked()` at `message_delivery.py:64-69` immediately returns a static `BLOCKED_RESPONSE` with no retry attempt.

### Spec

#### 6.1 Add Retry Mechanism

**Approach:** Add a `retry_count` field to `HealthCoachState` and a new `retry_with_constraints` node.

**File:** `src/graph/state.py` — Add field:
```python
retry_count: int  # 0 initially, incremented on blocked retry
```

**File:** `src/graph/nodes/message_delivery.py` — Add new node:

```python
async def retry_with_constraints(state, *, llm=None):
    """Retry a blocked message with an augmented safety-focused prompt."""
    # Augment the system prompt with explicit constraints
    augmented_prompt = (
        "IMPORTANT: Your previous response was flagged by the safety system. "
        "Rephrase your response focusing ONLY on general wellness, exercise, "
        "and goal-setting. Do NOT mention medical conditions, medications, "
        "diagnoses, or treatments. Redirect clinical questions to the care team."
    )
    # Re-invoke LLM with augmented prompt
    # Return new response for safety re-check
    return {"retry_count": state.get("retry_count", 0) + 1, ...}
```

**File:** `src/graph/router.py` — Modify safety routing:

Replace the current direct edge from `safety_check` to `output_blocked` with a conditional that checks retry count:

```python
def _route_by_safety_with_retry(state):
    safety_result = state.get("safety_result", {})
    action = safety_result.get("action", "passed")
    retry_count = state.get("retry_count", 0)

    if action == "blocked" and retry_count == 0:
        return "retry"
    # ... standard routing for passed/rewritten/blocked/escalated

graph.add_conditional_edges(
    "safety_check",
    _route_by_safety_with_retry,
    {
        "passed": "output_passed",
        "rewritten": "output_rewritten",
        "blocked": "output_blocked",
        "escalated": "output_escalated",
        "retry": "retry_with_constraints",
    },
)
# retry_with_constraints loops back to the active subgraph
graph.add_edge("retry_with_constraints", "active_subgraph")
# active_subgraph then goes to safety_check again (existing edge)
```

The flow becomes:
```
safety_check → BLOCKED (retry_count=0) → retry_with_constraints → active_subgraph → safety_check
safety_check → BLOCKED (retry_count=1) → output_blocked (static response, no more retries)
```

#### 6.2 Scope

- Only retry for `BLOCKED` action (not `ESCALATED` — crisis never retries)
- Only retry once (`retry_count < 1`)
- Only retry in ACTIVE and RE_ENGAGING phases (ONBOARDING blocked messages go straight to fallback)
- The retry routes back through the **same subgraph** that produced the message, so the tool loop can function

### Files to Modify

| File | Changes |
|---|---|
| `src/graph/state.py` | Add `retry_count: int` field |
| `src/graph/nodes/message_delivery.py` | Add `retry_with_constraints` node |
| `src/graph/router.py` | Add retry conditional edge, add retry node |

---

## 7. Phase 6: SSE Streaming Completion

### Problem

The SSE streaming endpoint at `src/main.py:222-258` emits `token`, `tool_start`, `tool_end`, `done`, and `error` events. The spec also requires a `phase_change` event, which is never emitted.

### Spec

#### 7.1 Emit `phase_change` Event

**File:** `src/main.py`

In the `event_generator()` loop (lines 222-258), add handling for the `check_phase_transition` node output:

```python
elif kind == "on_chain_end":
    # Detect phase transitions from the phase transition node
    output = event.get("data", {}).get("output", {})
    if isinstance(output, dict) and "phase" in output:
        new_phase = output["phase"]
        yield {
            "event": "message",
            "data": json.dumps({
                "type": "phase_change",
                "phase": new_phase,
            }),
        }
```

#### 7.2 Emit Tool Results

Currently `tool_end` only sends the tool name. The frontend's `SSEEvent` type expects a `result` field:

```python
elif kind == "on_tool_end":
    tool_name = event.get("name", "")
    tool_output = event.get("data", {}).get("output", "")
    yield {
        "event": "message",
        "data": json.dumps({
            "type": "tool_end",
            "tool": tool_name,
            "result": str(tool_output),
        }),
    }
```

#### 7.3 Emit Tool Arguments

Similarly for `tool_start`:

```python
elif kind == "on_tool_start":
    tool_name = event.get("name", "")
    tool_input = event.get("data", {}).get("input", {})
    yield {
        "event": "message",
        "data": json.dumps({
            "type": "tool_start",
            "tool": tool_name,
            "args": tool_input,
        }),
    }
```

#### 7.4 Use `json.dumps` Instead of f-strings

Replace all f-string JSON construction with `json.dumps()` to avoid escaping issues. The current `_escape_json()` helper is fragile. Use:

```python
import json

yield {
    "event": "message",
    "data": json.dumps({"type": "token", "content": chunk.content}),
}
```

### Files to Modify

| File | Changes |
|---|---|
| `src/main.py` | Add phase_change event, add tool args/results, use json.dumps |

---

## 8. Phase 7: LLM Wiring in Main App

### Problem

No `ChatAnthropic` instance is ever created in the application. All three subgraphs have an `if not llm:` fallback that returns a hardcoded string — this fallback is what currently runs in production. The LLM is never passed through.

### Spec

#### 8.1 Create LLM Instance at Startup

**File:** `src/main.py`

In the `lifespan()` function, create the shared LLM instance:

```python
from langchain_anthropic import ChatAnthropic

_llm_instance: Any = None

@asynccontextmanager
async def lifespan(application):
    global _llm_instance, _checkpointer

    settings = get_settings()

    # Initialize LLM
    _llm_instance = ChatAnthropic(
        model=settings.llm_model,           # "claude-haiku-4-5-20251001"
        temperature=settings.llm_temperature, # 0.7
        max_tokens=settings.llm_max_tokens,   # 1024
        streaming=True,                        # Required for astream_events
    )

    # Initialize checkpointer (Phase 2)
    # Initialize repos (Phase 3)
    # ... etc

    yield
```

#### 8.2 Pass LLM to Graph Builder

```python
def get_graph() -> Any:
    global _graph_instance
    if _graph_instance is None:
        _graph_instance = build_graph(
            llm=_llm_instance,
            checkpointer=_checkpointer,
            repos=get_repos(),
        )
    return _graph_instance
```

#### 8.3 Separate Safety LLM

The safety classifier uses different settings (temperature 0.0, max_tokens 256). It already creates its own `ChatAnthropic` instance inside `tier2_classify()` at `src/safety/classifier.py:40-44`. This is fine — it should remain separate from the conversation LLM.

### Files to Modify

| File | Changes |
|---|---|
| `src/main.py` | Create `_llm_instance` in lifespan, pass to `build_graph()` |
| `src/graph/router.py` | Accept `llm` param, pass to subgraph builders |

---

## 9. Phase 8: Missing Test Files

### Problem

The CLAUDE.md test structure specifies 23 test files. The project has 16. Missing:

| Missing File | Required By Spec | Current Coverage |
|---|---|---|
| `test_demo.py` | 5 demo readiness tests | Not covered |
| `test_concurrent.py` | Concurrency/state leakage | 3 tests in `test_error_recovery.py` |
| `test_models.py` | Pydantic model validation | 15 tests in `test_state.py` |
| `test_config.py` | Configuration tests | Not covered |
| `safe_prompts.json` | Separate safe prompt bank for FP testing | 16 safe prompts embedded in `adversarial_prompts.json` |

### Spec

#### 9.1 Create `tests/test_demo.py`

5 tests for demo readiness:

1. `test_demo_seed_data_loads` — Verify `src/db/seed.py` produces 3 patients with correct phases
2. `test_demo_patient_journey_sarah` — Sarah (ACTIVE) can chat and get adherence summary
3. `test_demo_patient_journey_marcus` — Marcus (ONBOARDING) can set a goal
4. `test_demo_patient_journey_elena` — Elena (RE_ENGAGING) receives re-engagement message
5. `test_demo_all_endpoints_respond` — Hit all 7 endpoints with mock auth and verify no 500s

#### 9.2 Create `tests/test_concurrent.py`

Move the 3 concurrent tests from `test_error_recovery.py` and add:

1. `test_different_users_get_different_routing` (moved)
2. `test_consent_gate_independent_per_user` (moved)
3. `test_concurrent_safety_checks_independent` (moved)
4. `test_concurrent_tool_calls_no_state_leakage` — Two users calling set_goal simultaneously
5. `test_concurrent_phase_transitions_isolated` — Two users transitioning phases simultaneously
6. `test_concurrent_rate_limiting_per_user` — Rate limits are per-user, not global
7. `test_concurrent_checkpointer_thread_isolation` — Checkpointer threads don't cross

#### 9.3 Create `tests/test_models.py`

15 tests for Pydantic model validation:

1-7. `PatientProfile`, `Goal`, `Milestone`, `Reminder`, `ConversationTurn`, `SafetyAuditEntry`, `ClinicianAlert` — validate required fields, defaults, UUID generation
8-11. Enum validation — `PhaseState`, `SafetyClassificationType`, `SafetyAction`, `AlertUrgency`
12. `SafetyResult` — structured output schema
13. `ConversationSummary` — turn range validation
14-15. Edge cases — invalid enum values, missing required fields

#### 9.4 Create `tests/test_config.py`

Configuration tests:

1. `test_default_settings` — All defaults are correct
2. `test_re_engage_days_parsing` — "2,5,7" parses to [2,5,7]
3. `test_cors_origins_parsing` — Comma-separated origins parse correctly
4. `test_env_file_loading` — Settings load from .env
5. `test_model_config_values` — LLM model, temperature, max_tokens defaults

#### 9.5 Create `tests/safe_prompts.json`

Extract the 16 safe prompts from `adversarial_prompts.json` into a separate file, and add more to reach 50+:

Categories:
- Exercise questions (15): "How many push-ups should I do?", "Can I walk instead of run?"
- Goal-setting (10): "I want to exercise 3 times a week", "Let's set a new goal"
- Motivation (10): "I'm feeling unmotivated today", "I need encouragement"
- Scheduling (10): "Remind me to stretch on Monday", "When should I exercise?"
- Progress (5): "How am I doing this week?", "What's my streak?"

### Files to Create

| File | Tests |
|---|---|
| `tests/test_demo.py` | 5 |
| `tests/test_concurrent.py` | 7+ |
| `tests/test_models.py` | 15 |
| `tests/test_config.py` | 5 |
| `tests/safe_prompts.json` | 50+ prompts |

---

## 10. Phase 9: Frontend Upgrade & Integration

### Problem

The frontend at `web/` is a 100% mocked demo. Every component works visually but:

- **Zero API calls** — No `fetch()`, no `EventSource`, no HTTP client anywhere
- **All responses hardcoded** — `lib/demo-responses.ts` has pre-scripted responses per patient
- **Streaming simulated** — `simulateStream()` uses `setTimeout` to emit words at 30-80ms
- **No auth** — No Supabase Auth, no JWT tokens, no login flow
- **No state persistence** — Patient data loaded from `lib/demo-data.ts` on every page load
- **Patient switching is demo-only** — Dropdown selects between 3 hardcoded patients

### 10.1 New Dependencies

Add to `web/package.json`:

```json
{
  "@supabase/supabase-js": "^2.45.0",
  "@supabase/auth-ui-react": "^0.4.7",
  "@supabase/auth-ui-shared": "^0.1.8"
}
```

### 10.2 Environment Configuration

Create `web/.env.local.example`:

```bash
NEXT_PUBLIC_SUPABASE_URL=https://xxxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 10.3 Supabase Client

Create `web/lib/supabase.ts`:

```typescript
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
)
```

### 10.4 API Client

Create `web/lib/api.ts`:

A typed API client that wraps `fetch` with auth headers from Supabase session:

```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

async function getAuthHeaders(): Promise<Record<string, string>> {
  const { data: { session } } = await supabase.auth.getSession()
  if (!session) throw new Error('Not authenticated')
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  }
}

export async function fetchProfile(): Promise<ProfileResponse> { ... }
export async function fetchGoals(): Promise<GoalResponse> { ... }
export async function fetchConversation(limit?, offset?): Promise<ConversationResponse> { ... }
export async function grantConsent(version: string): Promise<ConsentResponse> { ... }
export function streamChat(message: string): EventSource { ... }
```

### 10.5 Auth Provider & Login

Create `web/components/auth/auth-provider.tsx`:

A context provider that wraps the app with Supabase auth state:

```typescript
'use client'
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'
import type { Session, User } from '@supabase/supabase-js'

interface AuthContext {
  user: User | null
  session: Session | null
  loading: boolean
  signOut: () => Promise<void>
}

export function AuthProvider({ children }) {
  // Listen to onAuthStateChange
  // Provide session/user to children
}
```

Create `web/components/auth/login-form.tsx`:

A login form using Supabase Auth UI or custom email/password form. This replaces the current "Demo Mode" badge — real users log in.

### 10.6 Rewrite Chat Container

**File:** `web/components/chat/chat-container.tsx`

This is the largest change. Replace the entire demo response flow with real SSE streaming.

**Current flow (mock):**
```
handleSend() → demoResponses[patientId] → simulateStream() → update state
```

**New flow (real):**
```
handleSend() → POST /api/chat (SSE) → parse events → update state
```

Key changes:

```typescript
async function handleSend(text: string) {
  // 1. Add user message to local state
  const userMsg = { id: crypto.randomUUID(), role: 'user', content: text, ... }
  setMessages(prev => [...prev, userMsg])

  // 2. Create empty assistant message
  const assistantId = crypto.randomUUID()
  const assistantMsg = { id: assistantId, role: 'assistant', content: '', isStreaming: true, tool_calls: [] }
  setMessages(prev => [...prev, assistantMsg])
  setIsStreaming(true)

  // 3. Open SSE connection
  const headers = await getAuthHeaders()
  const response = await fetch(`${API_URL}/api/chat`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ message: text }),
  })

  const reader = response.body!.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const data = JSON.parse(line.slice(6)) as SSEEvent

      switch (data.type) {
        case 'token':
          // Append token to assistant message content
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, content: m.content + data.content }
              : m
          ))
          break

        case 'tool_start':
          // Add tool call with "running" status
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, tool_calls: [...(m.tool_calls || []),
                  { tool: data.tool!, args: data.args || {}, status: 'running' }
                ]}
              : m
          ))
          break

        case 'tool_end':
          // Update tool call to "complete" with result
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, tool_calls: m.tool_calls?.map(tc =>
                  tc.tool === data.tool
                    ? { ...tc, status: 'complete', result: data.result }
                    : tc
                )}
              : m
          ))
          break

        case 'phase_change':
          // Add phase change banner
          onPhaseChange?.(data.phase!)
          setEvents(prev => [...prev, {
            type: 'phase_change',
            phaseChange: { from: currentPhase, to: data.phase! }
          }])
          break

        case 'done':
          // Mark message as done streaming
          setMessages(prev => prev.map(m =>
            m.id === assistantId ? { ...m, isStreaming: false } : m
          ))
          setIsStreaming(false)
          break

        case 'error':
          // Show error, stop streaming
          setMessages(prev => prev.map(m =>
            m.id === assistantId
              ? { ...m, content: m.content || 'Something went wrong. Please try again.', isStreaming: false }
              : m
          ))
          setIsStreaming(false)
          break
      }
    }
  }
}
```

### 10.7 Rewrite Home Page

**File:** `web/app/page.tsx`

Replace demo data loading with real API calls:

```typescript
'use client'
import { useEffect, useState } from 'react'
import { useAuth } from '@/components/auth/auth-provider'
import { fetchProfile, fetchGoals, fetchConversation } from '@/lib/api'

export default function Home() {
  const { user, session, loading: authLoading } = useAuth()
  const [profile, setProfile] = useState<Profile | null>(null)
  const [goals, setGoals] = useState<Goal[]>([])
  const [conversation, setConversation] = useState<Message[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!session) return
    async function loadData() {
      const [profileData, goalsData, convoData] = await Promise.all([
        fetchProfile(),
        fetchGoals(),
        fetchConversation(50),
      ])
      setProfile(profileData)
      setGoals(goalsData.goals)
      setConversation(convoData.turns)
      setLoading(false)
    }
    loadData()
  }, [session])

  // Show login if not authenticated
  if (!session) return <LoginForm />

  // Show loading state
  if (loading) return <LoadingScreen />

  // Render app with real data
  return (
    <div className="flex h-full flex-col">
      <Header profile={profile} />
      {!profile?.consent_given && <ConsentBanner onConsent={handleConsent} />}
      <main>
        <PatientSidebar
          profile={profile}
          goals={goals}
          adherence={...}  // from profile or goals data
        />
        <ChatContainer
          initialMessages={conversation}
          disabled={!profile?.consent_given}
          currentPhase={profile?.phase}
        />
      </main>
    </div>
  )
}
```

### 10.8 Update Consent Banner

**File:** `web/components/consent-banner.tsx`

Wire `onConsent` to real API:

```typescript
async function handleConsent() {
  await grantConsent('1.0')
  // Refresh profile to get new phase
  const updatedProfile = await fetchProfile()
  setProfile(updatedProfile)
}
```

### 10.9 Update Patient Sidebar

**File:** `web/components/sidebar/patient-sidebar.tsx`

Change props from `{ patient: Patient }` to `{ profile, goals, adherence }` to accept real API data shapes. The component structure stays the same — just the data source changes.

### 10.10 Remove Demo Mode

Files to delete or gut:
- `web/lib/demo-data.ts` — Delete (or keep as fallback for offline dev)
- `web/lib/demo-responses.ts` — Delete
- `web/components/patient-switcher.tsx` — Remove (single authenticated user, no switching)
- Remove "Demo Mode" badge from header

### 10.11 Add Loading & Error States

Currently no loading or error handling exists. Add:

- **Loading skeleton** for chat messages while `fetchConversation` resolves
- **Loading skeleton** for sidebar while `fetchProfile`/`fetchGoals` resolve
- **Error boundary** around chat container for failed API calls
- **Reconnection logic** for SSE disconnects (retry with exponential backoff)
- **Offline indicator** when API is unreachable

### 10.12 Add Real-Time Goal Updates

When the LLM calls `set_goal` during a conversation, the sidebar should update. Two approaches:

- **Option A (simple):** Refetch goals after each `done` SSE event
- **Option B (reactive):** Parse `tool_end` events for `set_goal` tool and update goals state directly

Option A is simpler and more reliable.

### 10.13 Component Changes Summary

| Component | Change Type | Details |
|---|---|---|
| `app/layout.tsx` | Wrap with `AuthProvider` | Auth context for all pages |
| `app/page.tsx` | Major rewrite | Real API data loading, auth check, remove demo data |
| `chat-container.tsx` | Major rewrite | Real SSE streaming, remove simulateStream/demoResponses |
| `message-bubble.tsx` | No change | Already renders correct shapes |
| `message-input.tsx` | No change | Already handles send/disabled correctly |
| `tool-call-card.tsx` | Minor update | Handle string results from real tools (currently expects objects) |
| `typing-indicator.tsx` | No change | Works as-is |
| `phase-banner.tsx` | No change | Works as-is |
| `consent-banner.tsx` | Minor update | Wire to real POST /api/consent |
| `patient-switcher.tsx` | Delete | No longer needed (single auth user) |
| `patient-sidebar.tsx` | Props change | Accept profile+goals instead of Patient |
| `goal-card.tsx` | Minor update | Adapt to real goal shape from API |
| `adherence-stats.tsx` | Minor update | Adapt to real adherence data |
| `phase-badge.tsx` | No change | Works as-is |

### 10.14 New Files

| File | Purpose |
|---|---|
| `web/lib/supabase.ts` | Supabase client instance |
| `web/lib/api.ts` | Typed API client with auth headers |
| `web/components/auth/auth-provider.tsx` | Auth context provider |
| `web/components/auth/login-form.tsx` | Login/signup form |
| `web/.env.local.example` | Environment variable template |

---

## 11. Dependency Order & Execution Strategy

### Dependency Graph

```
Phase 7 (LLM Wiring) ──────────────┐
Phase 3 (Repository Wiring) ────────┤
Phase 2 (Checkpointer) ────────────┤
                                    ↓
Phase 1 (Tool Binding) ────── requires LLM + repos
                                    ↓
Phase 4 (Summarization) ────── requires LLM + repos wired
Phase 5 (Safety Retry) ────── requires tool loop working
Phase 6 (SSE Completion) ──── requires tools emitting events
                                    ↓
Phase 8 (Missing Tests) ────── requires backend working
                                    ↓
Phase 9 (Frontend) ──────────── requires all backend phases complete
```

### Recommended Execution Order

**Block 1 — Foundation (do first, in parallel)**
1. Phase 7: LLM Wiring (create `_llm_instance`)
2. Phase 2: Checkpointer Integration (`AsyncPostgresSaver`)
3. Phase 3: Repository Wiring (`get_repos()` + `functools.partial`)

**Block 2 — Core Loop (depends on Block 1)**
4. Phase 1: Tool Binding & Execution Loop (subgraphs as StateGraphs)

**Block 3 — Refinements (depends on Block 2)**
5. Phase 4: Summarization Node (wire into graph)
6. Phase 5: Safety Retry Logic (blocked message retry)
7. Phase 6: SSE Streaming Completion (phase_change event, json.dumps)

**Block 4 — Quality (depends on Block 3)**
8. Phase 8: Missing Test Files (test_demo, test_concurrent, etc.)

**Block 5 — Frontend (depends on Block 3)**
9. Phase 9: Frontend Upgrade & Integration

### Verification Checkpoints

After each block, verify:

- **Block 1 done:** `uvicorn src.main:app` starts without errors, LLM instance created, checkpointer tables created, repos initialized
- **Block 2 done:** Send a chat message via `/api/chat/sync`, receive a real LLM-generated response (not hardcoded fallback). Tool calls appear in response when appropriate.
- **Block 3 done:** Summarization triggers every 6 turns. Blocked messages retry once. SSE stream includes all 6 event types.
- **Block 4 done:** `pytest` passes with 300+ tests, all spec files present
- **Block 5 done:** Frontend loads, authenticates, sends real messages, displays streamed responses with tool calls and phase transitions

### Estimated File Changes

| Category | Files Modified | Files Created | Files Deleted |
|---|---|---|---|
| Backend | 8 | 0 | 0 |
| Tests | 2 | 5 | 0 |
| Frontend | 7 | 4 | 2 |
| **Total** | **17** | **9** | **2** |
