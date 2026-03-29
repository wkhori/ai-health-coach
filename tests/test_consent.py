"""Tests for consent gate node."""

from langchain_core.messages import AIMessage, HumanMessage

from src.graph.nodes.consent_check import (
    CONSENT_REQUEST_MESSAGE,
    consent_gate_router,
    request_consent,
)
from src.graph.state import HealthCoachState


def _make_state(**overrides) -> HealthCoachState:
    """Create a default test state with overrides."""
    base: HealthCoachState = {
        "messages": [HumanMessage(content="hello")],
        "user_id": "test-user",
        "profile_id": "test-profile",
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
    base.update(overrides)
    return base


class TestConsentGateRouter:
    """Tests for consent gate routing logic."""

    def test_routes_to_no_consent_when_false(self):
        """User without consent gets routed to no_consent path."""
        state = _make_state(consent_given=False)
        assert consent_gate_router(state) == "no_consent"

    def test_routes_to_has_consent_when_true(self):
        """User with consent gets routed to has_consent path."""
        state = _make_state(consent_given=True)
        assert consent_gate_router(state) == "has_consent"

    def test_defaults_to_no_consent_when_missing(self):
        """Missing consent_given field defaults to no_consent."""
        state = _make_state()
        del state["consent_given"]  # type: ignore[misc]
        assert consent_gate_router(state) == "no_consent"


class TestRequestConsent:
    """Tests for the request_consent node."""

    def test_returns_consent_message(self):
        """Returns the consent request message as AIMessage."""
        state = _make_state(consent_given=False)
        result = request_consent(state)

        assert "messages" in result
        assert len(result["messages"]) == 1
        assert isinstance(result["messages"][0], AIMessage)

    def test_consent_message_content(self):
        """Consent message contains expected information."""
        state = _make_state(consent_given=False)
        result = request_consent(state)
        msg = result["messages"][0].content

        assert "consent" in msg.lower()
        assert "revoke" in msg.lower()

    def test_consent_response_text_set(self):
        """Response text is set in the result."""
        state = _make_state(consent_given=False)
        result = request_consent(state)
        assert result["response_text"] == CONSENT_REQUEST_MESSAGE

    def test_consent_blocks_unconsented_user(self):
        """A user without consent does NOT reach phase routing."""
        state = _make_state(consent_given=False, phase="ONBOARDING")
        # The consent gate router should still block even if phase is set
        assert consent_gate_router(state) == "no_consent"
