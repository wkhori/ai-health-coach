"""Deterministic phase routing — 100% application code, no LLM."""

from src.graph.state import HealthCoachState

# Valid phases for routing
VALID_PHASES = {"PENDING", "ONBOARDING", "ACTIVE", "RE_ENGAGING", "DORMANT"}

# Phase -> node name mapping
_PHASE_ROUTES = {
    "PENDING": "pending_response",
    "ONBOARDING": "onboarding_subgraph",
    "ACTIVE": "active_subgraph",
    "RE_ENGAGING": "re_engaging_subgraph",
    "DORMANT": "dormant_to_re_engaging",
}


def route_by_phase(state: HealthCoachState) -> str:
    """Route to the appropriate subgraph based on the current phase.

    This is deterministic application code. It reads state['phase'] and
    returns a node name string. The LLM is never involved in routing.
    """
    phase = state.get("phase", "PENDING")
    return _PHASE_ROUTES.get(phase, "pending_response")


def pending_response(state: HealthCoachState) -> dict:
    """Return a message for PENDING users (waiting for consent)."""
    from langchain_core.messages import AIMessage

    msg = "Welcome! We're getting everything set up for you. Please provide your consent to begin."
    return {
        "messages": [AIMessage(content=msg)],
        "response_text": msg,
    }


def dormant_to_re_engaging(state: HealthCoachState) -> dict:
    """Transition DORMANT users to RE_ENGAGING phase."""
    return {
        "phase": "RE_ENGAGING",
    }
