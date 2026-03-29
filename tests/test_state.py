"""Tests for graph state schema (HealthCoachState)."""

from langchain_core.messages import HumanMessage

from src.graph.state import HealthCoachState


class TestHealthCoachState:
    """Tests for the HealthCoachState TypedDict."""

    def test_state_has_messages_field(self):
        """State includes messages with add_messages annotation."""
        annotations = HealthCoachState.__annotations__
        assert "messages" in annotations

    def test_state_has_user_id(self):
        """State includes user_id string field."""
        annotations = HealthCoachState.__annotations__
        assert "user_id" in annotations

    def test_state_has_profile_id(self):
        """State includes profile_id string field."""
        assert "profile_id" in HealthCoachState.__annotations__

    def test_state_has_phase(self):
        """State includes phase string field."""
        assert "phase" in HealthCoachState.__annotations__

    def test_state_has_consent_given(self):
        """State includes consent_given bool field."""
        assert "consent_given" in HealthCoachState.__annotations__

    def test_state_has_conversation_summary(self):
        """State includes conversation_summary string field."""
        assert "conversation_summary" in HealthCoachState.__annotations__

    def test_state_has_turn_count(self):
        """State includes turn_count int field."""
        assert "turn_count" in HealthCoachState.__annotations__

    def test_state_has_active_goals(self):
        """State includes active_goals list field."""
        assert "active_goals" in HealthCoachState.__annotations__

    def test_state_has_adherence_summary(self):
        """State includes adherence_summary dict field."""
        assert "adherence_summary" in HealthCoachState.__annotations__

    def test_state_has_safety_result(self):
        """State includes safety_result dict field."""
        assert "safety_result" in HealthCoachState.__annotations__

    def test_state_has_is_scheduled_message(self):
        """State includes is_scheduled_message bool field."""
        assert "is_scheduled_message" in HealthCoachState.__annotations__

    def test_state_has_scheduled_message_type(self):
        """State includes scheduled_message_type string field."""
        assert "scheduled_message_type" in HealthCoachState.__annotations__

    def test_state_has_response_text(self):
        """State includes response_text string field."""
        assert "response_text" in HealthCoachState.__annotations__

    def test_state_can_be_instantiated(self):
        """State dict can be created with all required fields."""
        state: HealthCoachState = {
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
        assert state["user_id"] == "test-user"
        assert state["phase"] == "PENDING"
        assert len(state["messages"]) == 1

    def test_state_total_field_count(self):
        """State has exactly 14 fields (including retry_count)."""
        assert len(HealthCoachState.__annotations__) == 14
