"""Tests for phase routing (deterministic, no LLM)."""

from unittest.mock import MagicMock

from langchain_core.messages import AIMessage, HumanMessage

from src.graph.nodes.phase_router import (
    dormant_to_re_engaging,
    pending_response,
    route_by_phase,
)
from src.graph.nodes.phase_transition import (
    check_phase_transition,
    is_valid_transition,
)
from src.graph.state import HealthCoachState


def _make_state(**overrides) -> HealthCoachState:
    """Create a default test state with overrides."""
    base: HealthCoachState = {
        "messages": [HumanMessage(content="hello")],
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_id": "test-profile",
        "phase": "PENDING",
        "consent_given": True,
        "conversation_summary": "",
        "turn_count": 0,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
    }
    base.update(overrides)
    return base


class TestRouteByPhase:
    """Tests for deterministic phase routing."""

    def test_routes_pending_to_pending_response(self):
        state = _make_state(phase="PENDING")
        assert route_by_phase(state) == "pending_response"

    def test_routes_onboarding_to_onboarding_subgraph(self):
        state = _make_state(phase="ONBOARDING")
        assert route_by_phase(state) == "onboarding_subgraph"

    def test_routes_active_to_active_subgraph(self):
        state = _make_state(phase="ACTIVE")
        assert route_by_phase(state) == "active_subgraph"

    def test_routes_re_engaging_to_re_engaging_subgraph(self):
        state = _make_state(phase="RE_ENGAGING")
        assert route_by_phase(state) == "re_engaging_subgraph"

    def test_routes_dormant_to_re_engaging_transition(self):
        state = _make_state(phase="DORMANT")
        assert route_by_phase(state) == "dormant_to_re_engaging"

    def test_unknown_phase_defaults_to_pending(self):
        state = _make_state(phase="UNKNOWN_PHASE")
        assert route_by_phase(state) == "pending_response"

    def test_missing_phase_defaults_to_pending(self):
        state = _make_state()
        del state["phase"]  # type: ignore[misc]
        assert route_by_phase(state) == "pending_response"


class TestPendingResponse:
    """Tests for the pending_response node."""

    def test_returns_ai_message(self):
        state = _make_state(phase="PENDING")
        result = pending_response(state)
        assert "messages" in result
        assert isinstance(result["messages"][0], AIMessage)

    def test_returns_response_text(self):
        state = _make_state(phase="PENDING")
        result = pending_response(state)
        assert "response_text" in result
        assert result["response_text"] != ""


class TestDormantToReEngaging:
    """Tests for the dormant transition node."""

    def test_sets_phase_to_re_engaging(self):
        state = _make_state(phase="DORMANT")
        result = dormant_to_re_engaging(state)
        assert result["phase"] == "RE_ENGAGING"


class TestPhaseTransitions:
    """Tests for phase transition validation and execution."""

    # Valid transitions
    def test_valid_pending_to_onboarding(self):
        assert is_valid_transition("PENDING", "ONBOARDING") is True

    def test_valid_onboarding_to_active(self):
        assert is_valid_transition("ONBOARDING", "ACTIVE") is True

    def test_valid_active_to_re_engaging(self):
        assert is_valid_transition("ACTIVE", "RE_ENGAGING") is True

    def test_valid_re_engaging_to_active(self):
        assert is_valid_transition("RE_ENGAGING", "ACTIVE") is True

    def test_valid_re_engaging_to_dormant(self):
        assert is_valid_transition("RE_ENGAGING", "DORMANT") is True

    def test_valid_dormant_to_re_engaging(self):
        assert is_valid_transition("DORMANT", "RE_ENGAGING") is True

    # Invalid transitions
    def test_invalid_pending_to_active(self):
        assert is_valid_transition("PENDING", "ACTIVE") is False

    def test_invalid_onboarding_to_dormant(self):
        assert is_valid_transition("ONBOARDING", "DORMANT") is False

    def test_invalid_active_to_pending(self):
        assert is_valid_transition("ACTIVE", "PENDING") is False

    def test_invalid_same_phase(self):
        assert is_valid_transition("ACTIVE", "ACTIVE") is False


class TestCheckPhaseTransition:
    """Tests for the check_phase_transition node."""

    def test_pending_to_onboarding_with_consent(self):
        state = _make_state(phase="PENDING", consent_given=True)
        result = check_phase_transition(state)
        assert result.get("phase") == "ONBOARDING"

    def test_pending_stays_pending_without_consent(self):
        state = _make_state(phase="PENDING", consent_given=False)
        result = check_phase_transition(state)
        assert result == {}

    def test_onboarding_to_active_with_confirmed_goal(self):
        state = _make_state(
            phase="ONBOARDING",
            active_goals=[{"title": "Walk daily", "confirmed": True}],
        )
        result = check_phase_transition(state)
        assert result.get("phase") == "ACTIVE"

    def test_onboarding_stays_without_confirmed_goal(self):
        state = _make_state(
            phase="ONBOARDING",
            active_goals=[{"title": "Walk daily", "confirmed": False}],
        )
        result = check_phase_transition(state)
        assert result == {}

    def test_re_engaging_to_active_on_user_message(self):
        state = _make_state(phase="RE_ENGAGING", is_scheduled_message=False)
        result = check_phase_transition(state)
        assert result.get("phase") == "ACTIVE"

    def test_re_engaging_stays_on_scheduled_message(self):
        state = _make_state(phase="RE_ENGAGING", is_scheduled_message=True)
        result = check_phase_transition(state)
        assert result == {}

    def test_dormant_to_re_engaging_on_user_message(self):
        state = _make_state(phase="DORMANT", is_scheduled_message=False)
        result = check_phase_transition(state)
        assert result.get("phase") == "RE_ENGAGING"

    def test_persists_phase_to_db(self):
        """Phase change is persisted via profile_repo."""
        mock_repo = MagicMock()
        state = _make_state(phase="PENDING", consent_given=True, profile_id="prof-123")
        check_phase_transition(state, profile_repo=mock_repo)
        mock_repo.update_phase.assert_called_once()
