"""Tests for Pydantic model validation — all models in src/models/.

Minimum 15 tests required covering:
- Required fields, defaults, UUID generation
- Enum validation
- Safety result structured output
- ConversationSummary turn range
- Edge cases (invalid enums, missing fields)
"""

from datetime import date, datetime
from uuid import UUID, uuid4

import pytest

from src.models.alert import ClinicianAlert
from src.models.enums import (
    AlertUrgency,
    InteractionType,
    PhaseState,
    SafetyAction,
    SafetyClassificationType,
)
from src.models.goal import Goal, Milestone
from src.models.message import ConversationSummary, ConversationTurn
from src.models.patient import PatientProfile
from src.models.reminder import Reminder
from src.models.safety import SafetyAuditEntry, SafetyResult

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_GOAL_ID = UUID("00000000-0000-0000-0000-000000000002")


# ---------------------------------------------------------------------------
# 1-3: PatientProfile — required fields, defaults, consent property
# ---------------------------------------------------------------------------
class TestPatientProfile:
    def test_required_fields(self):
        """PatientProfile requires id, user_id, and display_name."""
        profile = PatientProfile(
            id=uuid4(),
            user_id=TEST_USER_ID,
            display_name="Test Patient",
        )
        assert profile.display_name == "Test Patient"
        assert isinstance(profile.id, UUID)

    def test_defaults(self):
        """PatientProfile has correct default values."""
        profile = PatientProfile(
            id=uuid4(),
            user_id=TEST_USER_ID,
            display_name="Test",
        )
        assert profile.timezone == "UTC"
        assert profile.phase == PhaseState.PENDING
        assert profile.consent_given_at is None
        assert profile.consent_revoked_at is None
        assert profile.consent_version is None
        assert profile.onboarding_completed_at is None
        assert profile.last_message_at is None
        assert isinstance(profile.created_at, datetime)
        assert isinstance(profile.updated_at, datetime)

    def test_has_consent_property(self):
        """has_consent returns True only when consent given and not revoked."""
        profile_no_consent = PatientProfile(
            id=uuid4(),
            user_id=TEST_USER_ID,
            display_name="Test",
        )
        assert profile_no_consent.has_consent is False

        profile_with_consent = PatientProfile(
            id=uuid4(),
            user_id=TEST_USER_ID,
            display_name="Test",
            consent_given_at=datetime.now(),
        )
        assert profile_with_consent.has_consent is True

        profile_revoked = PatientProfile(
            id=uuid4(),
            user_id=TEST_USER_ID,
            display_name="Test",
            consent_given_at=datetime.now(),
            consent_revoked_at=datetime.now(),
        )
        assert profile_revoked.has_consent is False


# ---------------------------------------------------------------------------
# 4-5: Goal and Milestone — required fields and defaults
# ---------------------------------------------------------------------------
class TestGoalModel:
    def test_goal_required_fields_and_defaults(self):
        """Goal requires user_id and title; other fields have defaults."""
        goal = Goal(
            user_id=TEST_USER_ID,
            title="Walk daily",
        )
        assert goal.user_id == TEST_USER_ID
        assert goal.title == "Walk daily"
        assert goal.description == ""
        assert goal.frequency == ""
        assert goal.target_per_week == 0
        assert goal.confirmed is False
        assert goal.status == "active"
        assert goal.target_date is None
        assert goal.milestones == []
        assert goal.id is None

    def test_milestone_required_fields(self):
        """Milestone requires goal_id, user_id, title, and week_number."""
        ms = Milestone(
            goal_id=TEST_GOAL_ID,
            user_id=TEST_USER_ID,
            title="Week 1: Walk 20 min",
            week_number=1,
        )
        assert ms.goal_id == TEST_GOAL_ID
        assert ms.week_number == 1
        assert ms.completed is False
        assert ms.completed_at is None


# ---------------------------------------------------------------------------
# 6-7: Reminder and ClinicianAlert — defaults
# ---------------------------------------------------------------------------
class TestReminderModel:
    def test_reminder_defaults(self):
        """Reminder has correct default values."""
        reminder = Reminder(user_id=TEST_USER_ID)
        assert reminder.reminder_type == "follow_up"
        assert reminder.message_template == ""
        assert reminder.status == "pending"
        assert reminder.retry_count == 0
        assert reminder.attempt_number == 1
        assert reminder.id is None

    def test_clinician_alert_defaults(self):
        """ClinicianAlert has correct default values."""
        alert = ClinicianAlert(
            user_id=TEST_USER_ID,
            alert_type="crisis",
        )
        assert alert.urgency == AlertUrgency.ROUTINE
        assert alert.status == "pending"
        assert alert.message == ""
        assert alert.acknowledged_at is None
        assert alert.notes is None


# ---------------------------------------------------------------------------
# 8-11: Enum validation
# ---------------------------------------------------------------------------
class TestEnumValidation:
    def test_phase_state_values(self):
        """PhaseState enum has exactly 5 values."""
        assert PhaseState.PENDING == "PENDING"
        assert PhaseState.ONBOARDING == "ONBOARDING"
        assert PhaseState.ACTIVE == "ACTIVE"
        assert PhaseState.RE_ENGAGING == "RE_ENGAGING"
        assert PhaseState.DORMANT == "DORMANT"
        assert len(PhaseState) == 5

    def test_safety_classification_type_values(self):
        """SafetyClassificationType has exactly 4 values."""
        assert SafetyClassificationType.SAFE == "safe"
        assert SafetyClassificationType.CLINICAL == "clinical"
        assert SafetyClassificationType.CRISIS == "crisis"
        assert SafetyClassificationType.AMBIGUOUS == "ambiguous"
        assert len(SafetyClassificationType) == 4

    def test_safety_action_values(self):
        """SafetyAction has exactly 4 values."""
        assert SafetyAction.PASSED == "passed"
        assert SafetyAction.REWRITTEN == "rewritten"
        assert SafetyAction.BLOCKED == "blocked"
        assert SafetyAction.ESCALATED == "escalated"
        assert len(SafetyAction) == 4

    def test_alert_urgency_values(self):
        """AlertUrgency has exactly 2 values."""
        assert AlertUrgency.ROUTINE == "routine"
        assert AlertUrgency.URGENT == "urgent"
        assert len(AlertUrgency) == 2


# ---------------------------------------------------------------------------
# 12: SafetyResult structured output schema
# ---------------------------------------------------------------------------
class TestSafetyResultSchema:
    def test_safety_result_structured_output(self):
        """SafetyResult works as a structured output schema for LLM classification."""
        result = SafetyResult(
            classification=SafetyClassificationType.SAFE,
            confidence=0.95,
            categories=["positive_reinforcement"],
            flagged_phrases=[],
            reasoning="Normal wellness message",
        )
        assert result.classification == SafetyClassificationType.SAFE
        assert result.confidence == 0.95
        assert result.categories == ["positive_reinforcement"]
        assert result.flagged_phrases == []
        assert result.reasoning == "Normal wellness message"

    def test_safety_result_defaults(self):
        """SafetyResult defaults for optional fields."""
        result = SafetyResult(
            classification=SafetyClassificationType.SAFE,
            confidence=0.9,
        )
        assert result.categories == []
        assert result.flagged_phrases == []
        assert result.reasoning == ""

    def test_safety_audit_entry_full(self):
        """SafetyAuditEntry contains all fields for the audit log."""
        entry = SafetyAuditEntry(
            user_id=TEST_USER_ID,
            input_text="Great job on your exercise!",
            classification=SafetyClassificationType.SAFE,
            confidence=0.99,
            action_taken=SafetyAction.PASSED,
            tier="rule",
        )
        assert entry.user_id == TEST_USER_ID
        assert entry.tier == "rule"
        assert entry.model_used == ""
        assert isinstance(entry.created_at, datetime)


# ---------------------------------------------------------------------------
# 13: ConversationSummary turn range
# ---------------------------------------------------------------------------
class TestConversationSummary:
    def test_conversation_summary_turn_range(self):
        """ConversationSummary captures turns_covered_from and turns_covered_to."""
        summary = ConversationSummary(
            user_id=TEST_USER_ID,
            summary_text="Patient discussed goals and made progress.",
            turns_covered_from=1,
            turns_covered_to=6,
        )
        assert summary.turns_covered_from == 1
        assert summary.turns_covered_to == 6
        assert summary.summary_text == "Patient discussed goals and made progress."

    def test_conversation_turn_fields(self):
        """ConversationTurn has all expected fields."""
        turn = ConversationTurn(
            user_id=TEST_USER_ID,
            role="user",
            content="Hello",
            phase="ONBOARDING",
        )
        assert turn.role == "user"
        assert turn.content == "Hello"
        assert turn.phase == "ONBOARDING"
        assert turn.turn_number == 0
        assert turn.tool_calls is None
        assert turn.tool_results is None


# ---------------------------------------------------------------------------
# 14-15: Edge cases — invalid values, missing required fields
# ---------------------------------------------------------------------------
class TestModelEdgeCases:
    def test_safety_result_confidence_out_of_range_high(self):
        """SafetyResult rejects confidence > 1.0."""
        with pytest.raises(ValueError, match="confidence must be between"):
            SafetyResult(
                classification=SafetyClassificationType.SAFE,
                confidence=1.5,
            )

    def test_safety_result_confidence_out_of_range_low(self):
        """SafetyResult rejects confidence < 0.0."""
        with pytest.raises(ValueError, match="confidence must be between"):
            SafetyResult(
                classification=SafetyClassificationType.SAFE,
                confidence=-0.1,
            )

    def test_safety_audit_entry_confidence_validated(self):
        """SafetyAuditEntry also validates confidence range."""
        with pytest.raises(ValueError, match="confidence must be between"):
            SafetyAuditEntry(
                user_id=TEST_USER_ID,
                input_text="test",
                classification=SafetyClassificationType.SAFE,
                confidence=2.0,
                action_taken=SafetyAction.PASSED,
            )

    def test_goal_missing_required_fields(self):
        """Goal without user_id or title raises ValidationError."""
        with pytest.raises(Exception):
            Goal()  # type: ignore[call-arg]

    def test_patient_profile_missing_required_fields(self):
        """PatientProfile without required fields raises ValidationError."""
        with pytest.raises(Exception):
            PatientProfile()  # type: ignore[call-arg]

    def test_safety_result_boundary_confidence_zero(self):
        """SafetyResult accepts confidence of exactly 0.0."""
        result = SafetyResult(
            classification=SafetyClassificationType.AMBIGUOUS,
            confidence=0.0,
        )
        assert result.confidence == 0.0

    def test_safety_result_boundary_confidence_one(self):
        """SafetyResult accepts confidence of exactly 1.0."""
        result = SafetyResult(
            classification=SafetyClassificationType.SAFE,
            confidence=1.0,
        )
        assert result.confidence == 1.0
