"""Phase transition logic — deterministic, application-code only."""

import contextlib
from typing import Any
from uuid import UUID

from src.graph.state import HealthCoachState
from src.models.enums import PhaseState

# Valid phase transitions
VALID_TRANSITIONS: dict[str, set[str]] = {
    PhaseState.PENDING.value: {PhaseState.ONBOARDING.value},
    PhaseState.ONBOARDING.value: {PhaseState.ACTIVE.value},
    PhaseState.ACTIVE.value: {PhaseState.RE_ENGAGING.value},
    PhaseState.RE_ENGAGING.value: {PhaseState.ACTIVE.value, PhaseState.DORMANT.value},
    PhaseState.DORMANT.value: {PhaseState.RE_ENGAGING.value},
}


def is_valid_transition(from_phase: str, to_phase: str) -> bool:
    """Check if a phase transition is valid."""
    allowed = VALID_TRANSITIONS.get(from_phase, set())
    return to_phase in allowed


def check_phase_transition(
    state: HealthCoachState,
    *,
    profile_repo: Any = None,
) -> dict:
    """Check if the current state warrants a phase transition.

    Phase transitions are deterministic:
    - PENDING -> ONBOARDING: consent_given is True
    - ONBOARDING -> ACTIVE: at least 1 confirmed goal
    - RE_ENGAGING -> ACTIVE: user sends any message (already handled by graph entry)
    - DORMANT -> RE_ENGAGING: user sends any message (already handled by phase_router)
    """
    current_phase = state.get("phase", "PENDING")
    new_phase = current_phase

    if current_phase == PhaseState.PENDING.value:
        if state.get("consent_given", False):
            new_phase = PhaseState.ONBOARDING.value

    elif current_phase == PhaseState.ONBOARDING.value:
        # Check if at least 1 confirmed goal exists
        active_goals = state.get("active_goals", [])
        has_confirmed = any(g.get("confirmed", False) for g in active_goals)
        if has_confirmed:
            new_phase = PhaseState.ACTIVE.value

    elif current_phase == PhaseState.RE_ENGAGING.value:
        # If user sent a message (non-scheduled), transition to ACTIVE
        if not state.get("is_scheduled_message", False):
            new_phase = PhaseState.ACTIVE.value

    elif current_phase == PhaseState.DORMANT.value and not state.get("is_scheduled_message", False):
        new_phase = PhaseState.RE_ENGAGING.value

    # Only update if phase changed and transition is valid
    if new_phase != current_phase and is_valid_transition(current_phase, new_phase):
        # Persist phase change to DB if repo available
        if profile_repo and state.get("profile_id"):
            with contextlib.suppress(Exception):
                profile_repo.update_phase(state["profile_id"], PhaseState(new_phase))

        return {"phase": new_phase}

    return {}


def log_and_respond(
    state: HealthCoachState,
    *,
    conversation_repo: Any = None,
) -> dict:
    """Log the conversation turn and prepare final response."""
    response_text = state.get("response_text", "")
    user_id = state.get("user_id", "")
    phase = state.get("phase", "PENDING")
    turn_count = state.get("turn_count", 0)

    if conversation_repo and user_id and response_text:
        with contextlib.suppress(Exception):
            conversation_repo.add_turn(
                user_id=UUID(user_id),
                role="assistant",
                content=response_text,
                phase=phase,
                turn_number=turn_count + 1,
            )

    return {"turn_count": turn_count + 1}
