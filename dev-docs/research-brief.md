# Research Brief: AI Health Coach
**Date:** 2026-03-27
**Questions investigated:** 24
**Researchers:** 4 parallel Opus 4.6 agents

## High-Confidence Findings

### LangGraph (v1.1.3)
- Subgraphs as compiled StateGraphs added via `add_node`; route with `add_conditional_edges` or `Command`
- Deterministic phase transitions: routing function reads state and returns node name string (application code, not LLM)
- PostgreSQL checkpointer (`langgraph-checkpoint-postgres` v3.0.5) works directly with Supabase connection string
- Tool calling: `ChatAnthropic.bind_tools()` + `ToolNode` from `langgraph.prebuilt`
- Testing: pytest + mock at two levels (unit test nodes as functions, integration test graph flows)
- Gotchas: No parallel tool calls in subgraphs; keep nesting to 2 levels max; parent must have checkpointer

### Anthropic Claude SDK (v0.86.0)
- Claude Haiku 4.5: $1/$5 per MTok, 200k context, 64k output, sub-second TTFT (~0.66s)
- Tool calling: `@beta_tool` decorator + Tool Runner pattern (beta) for agentic loop
- Structured outputs: `output_config.format` with `json_schema` (constrained decoding, guaranteed compliance)
- Strict tool use: `strict: true` on tool definitions for schema-compliant tool calls
- Safety: No built-in content filtering API — use Claude Haiku as custom classifier with domain-specific categories
- Gotchas: Haiku may infer missing parameters instead of asking; tool_result must come first in user message content array

### Healthcare Compliance & Safety
- FDA General Wellness exemption (updated Jan 2026): applies if software is unrelated to diagnosis/treatment
- HIPAA: triggered if any PHI is processed — BAA required with MedBridge
- FTC Health Breach Notification Rule: unauthorized disclosure of health data = breach (even to analytics)
- C-SSRS framework for crisis detection: 6 severity levels with language signals
- Woebot shut down June 2025 — FDA has no pathway for LLM-based therapy tools
- Safety classifier: layered approach — medical NER + intent classification + topic rails
- MedBridge GO: patient-facing mobile app for HEP, 90M+ programs, 8K+ exercises, HIPAA-compliant, Epic integration

### Supabase + FastAPI
- supabase-py v2.28.3: active, all features (Auth, Storage, Realtime, Edge Functions)
- pg_cron + pg_net for scheduled follow-ups — native, no external scheduler needed
- Two-client pattern: service_role admin client + per-request user client with JWT
- Hybrid approach viable: supabase-py for Auth/Storage + asyncpg for high-frequency DB ops
- Prisma Python is DEPRECATED (archived April 2025) — do not use
- Conversation schema: conversations + messages + tool_calls + scheduled_followups tables with JSONB metadata

## Unresolved Questions
- Exact MedBridge API integration pattern (no public API docs found — tool stubs are acceptable per brief)
- LangGraph + Anthropic Tool Runner interop (Tool Runner is Anthropic SDK-native; LangGraph uses langchain_anthropic)
- pg_cron granularity for dynamic scheduling (cron syntax doesn't support "send in 47 minutes" — need polling pattern)

## Key Constraints Discovered
- FDA General Wellness lane is safe ONLY if we never make disease-specific claims
- MedBridge data integration triggers HIPAA — even for non-clinical coaching
- Crisis detection is mandatory even for non-mental-health tools (post-surgical patients may express distress)
- LangGraph uses `langchain_anthropic.ChatAnthropic`, not raw Anthropic SDK — this affects tool calling patterns
- Consent must be granular, ongoing, and separate from MedBridge's own consent
