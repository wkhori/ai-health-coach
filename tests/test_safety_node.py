"""Tests for the safety check node and output handler in graph context."""

from langchain_core.messages import AIMessage, HumanMessage

from src.graph.nodes.message_delivery import (
    BLOCKED_RESPONSE,
    CRISIS_RESPONSE,
    output_blocked,
    output_escalated,
    output_passed,
    output_rewritten,
    route_by_safety,
)
from src.graph.nodes.safety_check import run_safety_check
from src.graph.state import HealthCoachState
from src.models.enums import SafetyAction


def _make_state(**overrides) -> HealthCoachState:
    base: HealthCoachState = {
        "messages": [
            HumanMessage(content="How are you?"),
            AIMessage(content="I'm doing well! How about you?"),
        ],
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_id": "test-profile",
        "phase": "ACTIVE",
        "consent_given": True,
        "conversation_summary": "",
        "turn_count": 5,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
    }
    base.update(overrides)
    return base


class TestRunSafetyCheck:
    """Tests for the safety check node."""

    def test_default_passes_without_classifier(self):
        """Without a classifier, all messages pass."""
        state = _make_state()
        result = run_safety_check(state)
        assert result["safety_result"]["action"] == SafetyAction.PASSED.value

    def test_calls_classifier_with_last_ai_message(self):
        """Classifier receives the last AI message text."""
        called_with = []

        def mock_classifier(text):
            called_with.append(text)
            return {
                "classification": "safe",
                "confidence": 0.95,
                "categories": [],
                "action": "passed",
            }

        state = _make_state()
        run_safety_check(state, safety_classifier=mock_classifier)
        assert called_with == ["I'm doing well! How about you?"]

    def test_returns_classifier_result(self):
        """Safety result from classifier is returned in state."""

        def mock_classifier(text):
            return {
                "classification": "clinical",
                "confidence": 0.7,
                "categories": ["medical_advice"],
                "action": "rewritten",
            }

        state = _make_state()
        result = run_safety_check(state, safety_classifier=mock_classifier)
        assert result["safety_result"]["classification"] == "clinical"
        assert result["safety_result"]["action"] == "rewritten"

    def test_handles_no_ai_messages(self):
        """Returns safe when there are no AI messages."""
        state = _make_state(messages=[HumanMessage(content="hello")])
        result = run_safety_check(state)
        assert result["safety_result"]["action"] == SafetyAction.PASSED.value

    def test_handles_empty_messages(self):
        """Returns safe when messages list is empty."""
        state = _make_state(messages=[])
        result = run_safety_check(state)
        assert result["safety_result"]["action"] == SafetyAction.PASSED.value


class TestRouteBySafety:
    """Tests for safety-based routing."""

    def test_routes_passed(self):
        state = _make_state(safety_result={"action": "passed"})
        assert route_by_safety(state) == "passed"

    def test_routes_rewritten(self):
        state = _make_state(safety_result={"action": "rewritten"})
        assert route_by_safety(state) == "rewritten"

    def test_routes_blocked(self):
        state = _make_state(safety_result={"action": "blocked"})
        assert route_by_safety(state) == "blocked"

    def test_routes_escalated(self):
        state = _make_state(safety_result={"action": "escalated"})
        assert route_by_safety(state) == "escalated"

    def test_default_routes_to_passed(self):
        state = _make_state(safety_result={})
        assert route_by_safety(state) == "passed"


class TestOutputHandlers:
    """Tests for output handler nodes."""

    def test_output_passed_returns_original(self):
        """Passed handler returns the original AI message content."""
        state = _make_state()
        result = output_passed(state)
        assert result["response_text"] == "I'm doing well! How about you?"

    def test_output_rewritten_returns_safe_message(self):
        """Rewritten handler returns the blocked response template."""
        state = _make_state()
        result = output_rewritten(state)
        assert result["response_text"] == BLOCKED_RESPONSE
        assert "care team" in result["response_text"].lower()

    def test_output_blocked_returns_safe_message(self):
        """Blocked handler returns the blocked response template."""
        state = _make_state()
        result = output_blocked(state)
        assert result["response_text"] == BLOCKED_RESPONSE

    def test_output_escalated_returns_crisis_response(self):
        """Escalated handler returns the hard-coded crisis response."""
        state = _make_state()
        result = output_escalated(state)
        assert result["response_text"] == CRISIS_RESPONSE

    def test_crisis_response_includes_hotline(self):
        """Crisis response includes the 988 hotline number."""
        assert "988" in CRISIS_RESPONSE

    def test_crisis_response_includes_care_team_alert(self):
        """Crisis response mentions care team has been alerted."""
        assert "care team" in CRISIS_RESPONSE.lower()

    def test_output_passed_empty_messages(self):
        """Passed handler with no AI messages returns empty string."""
        state = _make_state(messages=[HumanMessage(content="hi")])
        result = output_passed(state)
        assert result["response_text"] == ""
