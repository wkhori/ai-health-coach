"""Full patient journey tests — end-to-end simulations of patient lifecycles.

Tests simulate the complete journey:
PENDING -> consent -> ONBOARDING -> set goal -> ACTIVE -> check-in ->
re-engagement -> return -> ACTIVE

Uses mocked LLM and DB. 5+ tests required.
"""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID, uuid4

from langchain_core.messages import AIMessage, HumanMessage

from src.graph.nodes.consent_check import consent_gate_router
from src.graph.nodes.phase_router import dormant_to_re_engaging, route_by_phase
from src.graph.nodes.phase_transition import (
    check_phase_transition,
    is_valid_transition,
    log_and_respond,
)
from src.graph.nodes.safety_check import run_safety_check

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_state(**overrides) -> dict:
    """Create a minimal HealthCoachState dict for testing."""
    defaults = {
        "messages": [],
        "user_id": str(TEST_USER_ID),
        "profile_id": str(uuid4()),
        "phase": "PENDING",
        "consent_given": False,
        "conversation_summary": "",
        "turn_count": 0,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
    }
    defaults.update(overrides)
    return defaults


class TestFullJourneyPendingToActive:
    """Test the PENDING -> ONBOARDING -> ACTIVE journey."""

    def test_step1_pending_no_consent(self):
        """New patient starts in PENDING without consent."""
        state = _make_state(phase="PENDING", consent_given=False)

        # Consent gate should block
        result = consent_gate_router(state)
        assert result == "no_consent"

    def test_step2_consent_triggers_onboarding(self):
        """Granting consent transitions PENDING -> ONBOARDING."""
        state = _make_state(phase="PENDING", consent_given=True)

        result = check_phase_transition(state)
        assert result.get("phase") == "ONBOARDING"

    def test_step3_onboarding_routes_to_subgraph(self):
        """ONBOARDING phase routes to onboarding_subgraph."""
        state = _make_state(phase="ONBOARDING", consent_given=True)
        route = route_by_phase(state)
        assert route == "onboarding_subgraph"

    def test_step4_confirmed_goal_triggers_active(self):
        """Confirming a goal transitions ONBOARDING -> ACTIVE."""
        state = _make_state(
            phase="ONBOARDING",
            consent_given=True,
            active_goals=[{"title": "Walk daily", "confirmed": True}],
        )

        result = check_phase_transition(state)
        assert result.get("phase") == "ACTIVE"

    def test_step5_active_routes_to_active_subgraph(self):
        """ACTIVE phase routes to active_subgraph."""
        state = _make_state(phase="ACTIVE", consent_given=True)
        route = route_by_phase(state)
        assert route == "active_subgraph"


class TestFullJourneyActiveToReEngaging:
    """Test the ACTIVE -> RE_ENGAGING -> ACTIVE return journey."""

    def test_active_to_re_engaging_valid(self):
        """ACTIVE -> RE_ENGAGING is a valid transition."""
        assert is_valid_transition("ACTIVE", "RE_ENGAGING")

    def test_re_engaging_routes_to_subgraph(self):
        """RE_ENGAGING phase routes to re_engaging_subgraph."""
        state = _make_state(phase="RE_ENGAGING", consent_given=True)
        route = route_by_phase(state)
        assert route == "re_engaging_subgraph"

    def test_user_message_transitions_re_engaging_to_active(self):
        """User sending a message transitions RE_ENGAGING -> ACTIVE."""
        state = _make_state(
            phase="RE_ENGAGING",
            consent_given=True,
            is_scheduled_message=False,
            messages=[HumanMessage(content="I'm back!")],
        )

        result = check_phase_transition(state)
        assert result.get("phase") == "ACTIVE"

    def test_scheduled_message_stays_re_engaging(self):
        """Scheduled messages do NOT trigger RE_ENGAGING -> ACTIVE."""
        state = _make_state(
            phase="RE_ENGAGING",
            consent_given=True,
            is_scheduled_message=True,
        )

        result = check_phase_transition(state)
        assert result.get("phase", "RE_ENGAGING") == "RE_ENGAGING"


class TestFullJourneyReEngagingToDormant:
    """Test the RE_ENGAGING -> DORMANT -> RE_ENGAGING -> ACTIVE journey."""

    def test_re_engaging_to_dormant_valid(self):
        """RE_ENGAGING -> DORMANT is valid."""
        assert is_valid_transition("RE_ENGAGING", "DORMANT")

    def test_dormant_routes_to_re_engaging_handler(self):
        """DORMANT phase routes through dormant_to_re_engaging."""
        state = _make_state(phase="DORMANT", consent_given=True)
        route = route_by_phase(state)
        assert route == "dormant_to_re_engaging"

    def test_dormant_to_re_engaging_sets_phase(self):
        """dormant_to_re_engaging node sets phase to RE_ENGAGING."""
        state = _make_state(phase="DORMANT")
        result = dormant_to_re_engaging(state)
        assert result["phase"] == "RE_ENGAGING"

    def test_dormant_user_returns(self):
        """A DORMANT user sending a message transitions to RE_ENGAGING."""
        state = _make_state(
            phase="DORMANT",
            consent_given=True,
            is_scheduled_message=False,
        )

        result = check_phase_transition(state)
        assert result.get("phase") == "RE_ENGAGING"


class TestFullJourneyWithSafety:
    """Test safety checks at each stage of the journey."""

    def test_safety_passes_positive_response(self):
        """Positive coaching response passes safety."""
        state = _make_state(
            messages=[AIMessage(content="Great job on your exercise today!")],
        )

        def safe_classifier(text):
            return {
                "classification": "safe",
                "confidence": 0.99,
                "categories": ["positive_reinforcement"],
                "action": "passed",
                "reasoning": "Positive reinforcement",
            }

        result = run_safety_check(state, safety_classifier=safe_classifier)
        assert result["safety_result"]["action"] == "passed"

    def test_safety_blocks_clinical_response(self):
        """Clinical content in response gets blocked."""
        state = _make_state(
            messages=[AIMessage(content="Take 500 mg of ibuprofen twice daily")],
        )

        def clinical_classifier(text):
            return {
                "classification": "clinical",
                "confidence": 0.95,
                "categories": ["dosage"],
                "action": "rewritten",
                "reasoning": "Dosage pattern detected",
            }

        result = run_safety_check(state, safety_classifier=clinical_classifier)
        assert result["safety_result"]["action"] == "rewritten"

    def test_safety_escalates_crisis(self):
        """Crisis content triggers escalation."""
        state = _make_state(
            messages=[AIMessage(content="I understand you want to hurt yourself.")],
        )

        def crisis_classifier(text):
            return {
                "classification": "crisis",
                "confidence": 1.0,
                "categories": ["crisis"],
                "action": "blocked",
                "reasoning": "Crisis language detected",
            }

        result = run_safety_check(state, safety_classifier=crisis_classifier)
        assert result["safety_result"]["classification"] == "crisis"


class TestFullJourneyLogAndTransition:
    """Test logging and phase transitions at the end of each turn."""

    def test_turn_count_increments(self):
        """Turn count should increment after each turn."""
        state = _make_state(turn_count=5, response_text="Hello!")
        result = log_and_respond(state)
        assert result["turn_count"] == 6

    def test_log_with_conversation_repo(self):
        """When conversation_repo is available, turn is logged."""
        mock_repo = MagicMock()
        mock_repo.add_turn.return_value = None

        state = _make_state(
            turn_count=3,
            response_text="Keep up the great work!",
            phase="ACTIVE",
        )

        result = log_and_respond(state, conversation_repo=mock_repo)
        assert result["turn_count"] == 4
        mock_repo.add_turn.assert_called_once()

    def test_complete_journey_all_transitions(self):
        """Verify the full chain of valid transitions covers the complete lifecycle."""
        # PENDING -> ONBOARDING
        assert is_valid_transition("PENDING", "ONBOARDING")
        # ONBOARDING -> ACTIVE
        assert is_valid_transition("ONBOARDING", "ACTIVE")
        # ACTIVE -> RE_ENGAGING
        assert is_valid_transition("ACTIVE", "RE_ENGAGING")
        # RE_ENGAGING -> ACTIVE (user returns)
        assert is_valid_transition("RE_ENGAGING", "ACTIVE")
        # RE_ENGAGING -> DORMANT (3 attempts failed)
        assert is_valid_transition("RE_ENGAGING", "DORMANT")
        # DORMANT -> RE_ENGAGING (user returns)
        assert is_valid_transition("DORMANT", "RE_ENGAGING")

    def test_invalid_transitions_blocked(self):
        """Verify that skip-transitions are blocked."""
        # Cannot skip from PENDING -> ACTIVE
        assert not is_valid_transition("PENDING", "ACTIVE")
        # Cannot skip from ONBOARDING -> RE_ENGAGING
        assert not is_valid_transition("ONBOARDING", "RE_ENGAGING")
        # Cannot skip from ACTIVE -> DORMANT
        assert not is_valid_transition("ACTIVE", "DORMANT")
        # Cannot go backwards from ACTIVE -> ONBOARDING
        assert not is_valid_transition("ACTIVE", "ONBOARDING")
        # Cannot go from PENDING -> DORMANT
        assert not is_valid_transition("PENDING", "DORMANT")
