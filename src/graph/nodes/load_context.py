"""Load user profile, goals, and conversation summary from DB."""

from typing import Any
from uuid import UUID

from src.graph.state import HealthCoachState


def load_context(
    state: HealthCoachState,
    *,
    profile_repo: Any = None,
    goal_repo: Any = None,
    summary_repo: Any = None,
    conversation_repo: Any = None,
) -> dict:
    """Load user context from the database into graph state.

    Fetches the patient profile, active goals, latest conversation summary,
    and turn count. Repositories are injected for testability.
    """
    user_id = UUID(state["user_id"])

    # Load profile
    profile = profile_repo.get_by_user_id(user_id) if profile_repo else None

    if not profile:
        return {
            "phase": "PENDING",
            "consent_given": False,
            "profile_id": "",
            "conversation_summary": "",
            "turn_count": 0,
            "active_goals": [],
            "adherence_summary": {},
        }

    # Determine consent status
    consent_given = (
        profile.get("consent_given_at") is not None and profile.get("consent_revoked_at") is None
    )

    # Load active goals
    active_goals = []
    if goal_repo:
        active_goals = goal_repo.get_active_goals(user_id)

    # Load latest conversation summary
    conversation_summary = ""
    if summary_repo:
        latest = summary_repo.get_latest(user_id)
        if latest:
            conversation_summary = latest.get("summary_text", "")

    # Get turn count
    turn_count = 0
    if conversation_repo:
        turn_count = conversation_repo.get_turn_count(user_id)

    return {
        "phase": profile.get("phase", "PENDING"),
        "consent_given": consent_given,
        "profile_id": profile.get("id", ""),
        "conversation_summary": conversation_summary,
        "turn_count": turn_count,
        "active_goals": active_goals,
        "adherence_summary": {},
    }
