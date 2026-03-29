"""Main router graph assembly for the AI Health Coach."""

from functools import partial
from typing import Any

from langgraph.graph import END, START, StateGraph

from src.graph.nodes.consent_check import (
    consent_gate_router,
    request_consent,
)
from src.graph.nodes.message_delivery import (
    output_blocked,
    output_escalated,
    output_passed,
    output_rewritten,
    route_by_safety,
)
from src.graph.nodes.phase_router import (
    dormant_to_re_engaging,
    pending_response,
    route_by_phase,
)
from src.graph.nodes.phase_transition import (
    check_phase_transition,
    log_and_respond,
)
from src.graph.nodes.safety_check import run_safety_check
from src.graph.nodes.summarize import should_summarize, summarize_conversation
from src.graph.state import HealthCoachState


def _build_default_safety_classifier(safety_audit_repo: Any = None):
    """Build a safety classifier that chains Tier 1 + Tier 2 + audit logging."""

    def classify(text: str) -> dict:
        from src.safety.classifier import decide_action, tier2_classify
        from src.safety.rules import tier1_classify

        result = tier1_classify(text)
        tier = "tier1"
        if result is None:
            result = tier2_classify(text)
            tier = "tier2"

        action = decide_action(result)

        # Log to audit
        if safety_audit_repo:
            import contextlib

            with contextlib.suppress(Exception):
                safety_audit_repo.log_entry(
                    classification=result.classification.value
                    if hasattr(result.classification, "value")
                    else str(result.classification),
                    confidence=result.confidence,
                    action=action.value if hasattr(action, "value") else str(action),
                    tier=tier,
                    reasoning=result.reasoning,
                )

        return {
            "classification": result.classification.value
            if hasattr(result.classification, "value")
            else str(result.classification),
            "confidence": result.confidence,
            "categories": result.categories,
            "action": action.value if hasattr(action, "value") else str(action),
            "reasoning": result.reasoning,
        }

    return classify


def build_graph(
    *,
    llm: Any = None,
    load_context_fn: Any = None,
    onboarding_fn: Any = None,
    active_fn: Any = None,
    re_engaging_fn: Any = None,
    safety_check_fn: Any = None,
    log_and_respond_fn: Any = None,
    check_phase_transition_fn: Any = None,
    checkpointer: Any = None,
    repos: dict[str, Any] | None = None,
) -> Any:
    """Build and compile the main health coach graph.

    All node functions can be injected for testability.
    """
    from src.graph.nodes.load_context import load_context
    from src.graph.nodes.message_delivery import retry_with_constraints

    repos = repos or {}
    profile_repo = repos.get("profile")
    goal_repo = repos.get("goal")
    summary_repo = repos.get("summary")
    conversation_repo = repos.get("conversation")
    safety_audit_repo = repos.get("safety_audit")

    graph = StateGraph(HealthCoachState)

    # --- Build subgraphs ---
    if llm and not onboarding_fn:
        from src.graph.subgraphs.onboarding import build_onboarding_subgraph

        onboarding_node = build_onboarding_subgraph(llm)
    else:
        onboarding_node = onboarding_fn or _default_onboarding

    if llm and not active_fn:
        from src.graph.subgraphs.active import build_active_subgraph

        active_node = build_active_subgraph(llm)
    else:
        active_node = active_fn or _default_active

    if llm and not re_engaging_fn:
        from src.graph.subgraphs.re_engaging import build_re_engaging_subgraph

        re_engaging_node = build_re_engaging_subgraph(llm)
    else:
        re_engaging_node = re_engaging_fn or _default_re_engaging

    # --- Build safety classifier ---
    classifier = _build_default_safety_classifier(safety_audit_repo)

    # --- Add nodes ---
    graph.add_node(
        "load_context",
        load_context_fn
        or partial(
            load_context,
            profile_repo=profile_repo,
            goal_repo=goal_repo,
            summary_repo=summary_repo,
            conversation_repo=conversation_repo,
        ),
    )
    graph.add_node("request_consent", request_consent)
    graph.add_node("pending_response", pending_response)
    graph.add_node("onboarding_subgraph", onboarding_node)
    graph.add_node("active_subgraph", active_node)
    graph.add_node("re_engaging_subgraph", re_engaging_node)
    graph.add_node("dormant_to_re_engaging", dormant_to_re_engaging)
    graph.add_node(
        "safety_check",
        safety_check_fn
        or partial(
            run_safety_check,
            safety_classifier=classifier,
        ),
    )
    graph.add_node("output_passed", output_passed)
    graph.add_node("output_rewritten", output_rewritten)
    graph.add_node("output_blocked", output_blocked)
    graph.add_node("output_escalated", output_escalated)
    graph.add_node(
        "log_and_respond",
        log_and_respond_fn
        or partial(
            log_and_respond,
            conversation_repo=conversation_repo,
        ),
    )
    graph.add_node(
        "summarize",
        partial(
            summarize_conversation,
            llm=llm,
            summary_repo=summary_repo,
        ),
    )
    graph.add_node(
        "check_phase_transition",
        check_phase_transition_fn
        or partial(
            check_phase_transition,
            profile_repo=profile_repo,
        ),
    )
    graph.add_node(
        "retry_with_constraints",
        partial(retry_with_constraints, llm=llm),
    )

    # --- Edges ---

    # START -> load_context -> consent_gate
    graph.add_edge(START, "load_context")
    graph.add_conditional_edges(
        "load_context",
        consent_gate_router,
        {
            "has_consent": "phase_router_node",
            "no_consent": "request_consent",
        },
    )

    # request_consent -> END
    graph.add_edge("request_consent", END)

    # Add a dummy node for phase routing (conditional edge source)
    graph.add_node("phase_router_node", _passthrough)
    graph.add_conditional_edges(
        "phase_router_node",
        route_by_phase,
        {
            "pending_response": "pending_response",
            "onboarding_subgraph": "onboarding_subgraph",
            "active_subgraph": "active_subgraph",
            "re_engaging_subgraph": "re_engaging_subgraph",
            "dormant_to_re_engaging": "dormant_to_re_engaging",
        },
    )

    # pending_response -> END (no safety check needed for canned messages)
    graph.add_edge("pending_response", END)

    # Subgraphs -> safety_check
    graph.add_edge("onboarding_subgraph", "safety_check")
    graph.add_edge("active_subgraph", "safety_check")
    graph.add_edge("re_engaging_subgraph", "safety_check")

    # dormant_to_re_engaging -> re_engaging_subgraph
    graph.add_edge("dormant_to_re_engaging", "re_engaging_subgraph")

    # safety_check -> output_handler (conditional, with retry support)
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

    # retry_with_constraints loops back to safety_check for re-evaluation
    graph.add_edge("retry_with_constraints", "safety_check")

    # All output handlers -> log_and_respond
    graph.add_edge("output_passed", "log_and_respond")
    graph.add_edge("output_rewritten", "log_and_respond")
    graph.add_edge("output_blocked", "log_and_respond")
    graph.add_edge("output_escalated", "log_and_respond")

    # log_and_respond -> conditional summarization -> check_phase_transition -> END
    graph.add_conditional_edges(
        "log_and_respond",
        _should_summarize_router,
        {
            "summarize": "summarize",
            "skip": "check_phase_transition",
        },
    )
    graph.add_edge("summarize", "check_phase_transition")
    graph.add_edge("check_phase_transition", END)

    return graph.compile(checkpointer=checkpointer)


def _passthrough(state: HealthCoachState) -> dict:
    """No-op node used as a conditional edge source for phase routing."""
    return {}


def _should_summarize_router(state: HealthCoachState) -> str:
    """Route to summarize node or skip based on turn count."""
    if should_summarize(state, every_n=6):
        return "summarize"
    return "skip"


def _route_by_safety_with_retry(state: HealthCoachState) -> str:
    """Route based on safety classification, with retry support for blocked messages."""
    safety_result = state.get("safety_result", {})
    action = safety_result.get("action", "passed")
    retry_count = state.get("retry_count", 0)

    # If blocked (not escalated) and haven't retried yet, retry once
    if action == "blocked" and retry_count == 0:
        # Only retry in ACTIVE and RE_ENGAGING phases
        phase = state.get("phase", "")
        if phase in ("ACTIVE", "RE_ENGAGING"):
            return "retry"

    return route_by_safety(state)


async def _default_onboarding(state: HealthCoachState) -> dict:
    """Default onboarding placeholder."""
    from src.graph.subgraphs.onboarding import onboard_agent

    return await onboard_agent(state)


async def _default_active(state: HealthCoachState) -> dict:
    """Default active placeholder."""
    from src.graph.subgraphs.active import active_agent

    return await active_agent(state)


async def _default_re_engaging(state: HealthCoachState) -> dict:
    """Default re-engaging placeholder."""
    from src.graph.subgraphs.re_engaging import re_engage_agent

    return await re_engage_agent(state)
