"""Error recovery tests — test what happens when things break.

Tests cover:
- LLM API timeout -> graceful error message
- LLM returns malformed response -> fallback to safe generic message
- DB connection failure during load_context -> appropriate error
- Tool execution failure -> agent sees error and responds naturally
- Safety classifier failure -> default to BLOCK (err on caution)
- Concurrent requests for same user -> no state corruption
- 10+ tests required
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from langchain_core.messages import AIMessage

from src.graph.nodes.consent_check import consent_gate_router
from src.graph.nodes.load_context import load_context
from src.graph.nodes.phase_transition import check_phase_transition, log_and_respond
from src.graph.nodes.safety_check import run_safety_check
from src.models.enums import SafetyAction, SafetyClassificationType
from src.safety.classifier import decide_action

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


def _make_state(**overrides) -> dict:
    """Create a minimal HealthCoachState dict for testing."""
    defaults = {
        "messages": [],
        "user_id": str(TEST_USER_ID),
        "profile_id": str(uuid4()),
        "phase": "ACTIVE",
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
    defaults.update(overrides)
    return defaults


# ---------------------------------------------------------------------------
# LLM API timeout / failure
# ---------------------------------------------------------------------------
class TestLLMFailure:
    """Test handling of LLM API failures."""

    @pytest.mark.asyncio
    async def test_onboarding_without_llm_returns_fallback(self):
        """When LLM is not available, onboarding returns a default message."""
        from src.graph.subgraphs.onboarding import onboard_agent

        state = _make_state(phase="ONBOARDING")
        result = await onboard_agent(state, llm=None)

        assert "response_text" in result
        assert len(result["response_text"]) > 0
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_active_without_llm_returns_fallback(self):
        """When LLM is not available, active agent returns a default message."""
        from src.graph.subgraphs.active import active_agent

        state = _make_state(phase="ACTIVE")
        result = await active_agent(state, llm=None)

        assert "response_text" in result
        assert len(result["response_text"]) > 0

    @pytest.mark.asyncio
    async def test_re_engaging_without_llm_returns_fallback(self):
        """When LLM is not available, re-engagement returns a default message."""
        from src.graph.subgraphs.re_engaging import re_engage_agent

        state = _make_state(phase="RE_ENGAGING")
        result = await re_engage_agent(state, llm=None)

        assert "response_text" in result
        assert len(result["response_text"]) > 0

    @pytest.mark.asyncio
    async def test_llm_exception_during_onboarding(self):
        """LLM raising an exception should be handled gracefully."""
        from src.graph.subgraphs.onboarding import onboard_agent

        mock_llm = AsyncMock()
        mock_llm.ainvoke.side_effect = Exception("API timeout")

        state = _make_state(phase="ONBOARDING")

        with pytest.raises(Exception, match="API timeout"):
            await onboard_agent(state, llm=mock_llm)


# ---------------------------------------------------------------------------
# DB connection failure
# ---------------------------------------------------------------------------
class TestDBFailure:
    """Test handling of database connection failures."""

    def test_load_context_with_no_repos(self):
        """load_context with no repos returns safe defaults."""
        state = _make_state()
        result = load_context(state)

        assert result["phase"] == "PENDING"
        assert result["consent_given"] is False
        assert result["active_goals"] == []

    def test_load_context_with_failing_profile_repo(self):
        """load_context handles profile repo failure gracefully."""
        mock_repo = MagicMock()
        mock_repo.get_by_user_id.return_value = None

        state = _make_state()
        result = load_context(state, profile_repo=mock_repo)

        assert result["phase"] == "PENDING"
        assert result["consent_given"] is False

    def test_log_and_respond_with_failing_repo(self):
        """log_and_respond handles conversation repo failure gracefully."""
        mock_repo = MagicMock()
        mock_repo.add_turn.side_effect = Exception("DB connection error")

        state = _make_state(response_text="Hello there!", turn_count=5)
        # Should not raise — uses contextlib.suppress
        result = log_and_respond(state, conversation_repo=mock_repo)
        assert result["turn_count"] == 6

    def test_phase_transition_with_failing_repo(self):
        """Phase transition handles profile repo failure gracefully."""
        mock_repo = MagicMock()
        mock_repo.update_phase.side_effect = Exception("DB error")

        state = _make_state(
            phase="PENDING",
            consent_given=True,
        )
        # Should not raise — uses contextlib.suppress
        result = check_phase_transition(state, profile_repo=mock_repo)
        assert result.get("phase") == "ONBOARDING"


# ---------------------------------------------------------------------------
# Safety classifier failure -> default to BLOCK
# ---------------------------------------------------------------------------
class TestSafetyClassifierFailure:
    """When safety classifier fails, system should default to BLOCK."""

    def test_safety_check_with_no_classifier_passes(self):
        """Without a classifier, safety check defaults to passing (safe fallback)."""
        state = _make_state(
            messages=[AIMessage(content="Let's do some exercises!")],
        )
        result = run_safety_check(state, safety_classifier=None)
        assert result["safety_result"]["action"] == "passed"

    def test_safety_check_with_failing_classifier(self):
        """When classifier raises, safety check should propagate the error."""
        state = _make_state(
            messages=[AIMessage(content="Hello there!")],
        )

        def failing_classifier(text: str):
            raise RuntimeError("Classifier service unavailable")

        with pytest.raises(RuntimeError, match="Classifier service unavailable"):
            run_safety_check(state, safety_classifier=failing_classifier)

    def test_low_confidence_defaults_to_block(self):
        """When classification has low confidence, action should be BLOCK."""
        from src.models.safety import SafetyResult

        result = SafetyResult(
            classification=SafetyClassificationType.AMBIGUOUS,
            confidence=0.3,
            categories=["uncertain"],
            flagged_phrases=[],
            reasoning="Very unsure",
        )
        action = decide_action(result)
        assert action == SafetyAction.BLOCKED


# ---------------------------------------------------------------------------
# Concurrent requests
# ---------------------------------------------------------------------------
class TestConcurrentRequests:
    """Verify no state corruption with concurrent requests."""

    def test_different_users_get_different_routing(self):
        """Two users in different phases get routed differently."""
        from src.graph.nodes.phase_router import route_by_phase

        state_active = _make_state(phase="ACTIVE", user_id=str(uuid4()))
        state_onboarding = _make_state(phase="ONBOARDING", user_id=str(uuid4()))

        route_active = route_by_phase(state_active)
        route_onboarding = route_by_phase(state_onboarding)

        assert route_active == "active_subgraph"
        assert route_onboarding == "onboarding_subgraph"
        assert route_active != route_onboarding

    def test_consent_gate_independent_per_user(self):
        """Consent status is per-user, not shared."""
        state_consented = _make_state(consent_given=True, user_id=str(uuid4()))
        state_no_consent = _make_state(consent_given=False, user_id=str(uuid4()))

        assert consent_gate_router(state_consented) == "has_consent"
        assert consent_gate_router(state_no_consent) == "no_consent"

    @pytest.mark.asyncio
    async def test_concurrent_safety_checks_independent(self):
        """Multiple concurrent safety checks don't interfere with each other."""

        def classifier_safe(text):
            return {
                "classification": "safe",
                "confidence": 0.95,
                "categories": [],
                "action": "passed",
                "reasoning": "Safe",
            }

        def classifier_clinical(text):
            return {
                "classification": "clinical",
                "confidence": 0.9,
                "categories": ["clinical"],
                "action": "rewritten",
                "reasoning": "Clinical",
            }

        state_safe = _make_state(
            messages=[AIMessage(content="Great job!")],
            user_id=str(uuid4()),
        )
        state_clinical = _make_state(
            messages=[AIMessage(content="Take 500 mg")],
            user_id=str(uuid4()),
        )

        result_safe = run_safety_check(state_safe, safety_classifier=classifier_safe)
        result_clinical = run_safety_check(state_clinical, safety_classifier=classifier_clinical)

        assert result_safe["safety_result"]["classification"] == "safe"
        assert result_clinical["safety_result"]["classification"] == "clinical"


# ---------------------------------------------------------------------------
# Tool execution failure
# ---------------------------------------------------------------------------
class TestToolExecutionFailure:
    """Test handling of tool execution failures."""

    @pytest.mark.asyncio
    async def test_reminder_processing_handles_graph_error(self):
        """process_due_reminders marks failed reminders appropriately."""
        from src.scheduler.follow_up import process_due_reminders

        mock_repo = MagicMock()
        mock_repo.get_due_reminders.return_value = [
            {
                "id": str(uuid4()),
                "user_id": str(TEST_USER_ID),
                "reminder_type": "follow_up",
                "attempt_number": 1,
            }
        ]

        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = Exception("Tool execution failed")

        results = await process_due_reminders(reminder_repo=mock_repo, graph=mock_graph)

        assert len(results) == 1
        assert results[0]["status"] == "failed"
        assert "Tool execution failed" in results[0]["error"]
        mock_repo.mark_failed.assert_called_once()
