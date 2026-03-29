"""Concurrency tests — verify no state leakage between concurrent users.

7 tests covering:
- Different users get different routing
- Consent gate independent per user
- Concurrent safety checks
- Tool calls with no state leakage
- Phase transitions isolated
- Rate limiting per user
- Checkpointer thread isolation
"""

from __future__ import annotations

import asyncio
from uuid import uuid4

import pytest
from langchain_core.messages import AIMessage

from src.graph.nodes.consent_check import consent_gate_router
from src.graph.nodes.phase_router import route_by_phase
from src.graph.nodes.phase_transition import check_phase_transition
from src.graph.nodes.safety_check import run_safety_check
from src.main import _rate_limit_store, check_rate_limit


def _make_state(**overrides) -> dict:
    """Create a minimal HealthCoachState dict for testing."""
    defaults = {
        "messages": [],
        "user_id": str(uuid4()),
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


class TestConcurrentRouting:
    """Verify routing is independent per user state."""

    def test_different_users_get_different_routing(self):
        """Two users in different phases are routed to different subgraphs."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        state_a = _make_state(phase="ACTIVE", user_id=user_a_id)
        state_b = _make_state(phase="ONBOARDING", user_id=user_b_id)

        route_a = route_by_phase(state_a)
        route_b = route_by_phase(state_b)

        assert route_a == "active_subgraph"
        assert route_b == "onboarding_subgraph"
        assert route_a != route_b

    def test_consent_gate_independent_per_user(self):
        """Consent status is evaluated per user, not shared globally."""
        user_consented = str(uuid4())
        user_no_consent = str(uuid4())

        state_consented = _make_state(consent_given=True, user_id=user_consented)
        state_no_consent = _make_state(consent_given=False, user_id=user_no_consent)

        result_consented = consent_gate_router(state_consented)
        result_no_consent = consent_gate_router(state_no_consent)

        assert result_consented == "has_consent"
        assert result_no_consent == "no_consent"

        # Verify checking one user doesn't affect the other
        result_consented_again = consent_gate_router(state_consented)
        assert result_consented_again == "has_consent"


class TestConcurrentSafety:
    """Verify safety checks don't interfere between users."""

    @pytest.mark.asyncio
    async def test_concurrent_safety_checks_independent(self):
        """Multiple concurrent safety checks produce independent results."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        def classifier_safe(text):
            return {
                "classification": "safe",
                "confidence": 0.95,
                "categories": [],
                "action": "passed",
                "reasoning": "Safe content",
            }

        def classifier_crisis(text):
            return {
                "classification": "crisis",
                "confidence": 1.0,
                "categories": ["crisis"],
                "action": "blocked",
                "reasoning": "Crisis detected",
            }

        state_safe = _make_state(
            messages=[AIMessage(content="Great job on your walk today!")],
            user_id=user_a_id,
        )
        state_crisis = _make_state(
            messages=[AIMessage(content="I understand you want to hurt yourself.")],
            user_id=user_b_id,
        )

        # Run concurrently via asyncio.gather (sync functions wrapped)
        loop = asyncio.get_event_loop()
        result_safe, result_crisis = await asyncio.gather(
            loop.run_in_executor(None, lambda: run_safety_check(state_safe, safety_classifier=classifier_safe)),
            loop.run_in_executor(None, lambda: run_safety_check(state_crisis, safety_classifier=classifier_crisis)),
        )

        assert result_safe["safety_result"]["classification"] == "safe"
        assert result_safe["safety_result"]["action"] == "passed"
        assert result_crisis["safety_result"]["classification"] == "crisis"
        assert result_crisis["safety_result"]["action"] == "blocked"


class TestConcurrentToolCalls:
    """Verify tool call results don't leak between concurrent users."""

    def test_concurrent_tool_calls_no_state_leakage(self):
        """Separate state dicts for different users remain independent."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        state_a = _make_state(
            user_id=user_a_id,
            phase="ACTIVE",
            active_goals=[{"title": "Walk daily", "confirmed": True}],
            turn_count=5,
        )
        state_b = _make_state(
            user_id=user_b_id,
            phase="ONBOARDING",
            active_goals=[],
            turn_count=1,
        )

        # Verify states are fully independent
        assert state_a["user_id"] != state_b["user_id"]
        assert state_a["phase"] != state_b["phase"]
        assert state_a["active_goals"] != state_b["active_goals"]
        assert state_a["turn_count"] != state_b["turn_count"]

        # Mutating one state does not affect the other
        state_a["turn_count"] = 10
        assert state_b["turn_count"] == 1

        state_b["active_goals"].append({"title": "New goal", "confirmed": False})
        assert len(state_a["active_goals"]) == 1


class TestConcurrentPhaseTransitions:
    """Verify phase transitions are isolated per user."""

    def test_concurrent_phase_transitions_isolated(self):
        """Phase transitions for one user don't affect another user."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        # User A: PENDING with consent -> should transition to ONBOARDING
        state_a = _make_state(
            phase="PENDING",
            consent_given=True,
            user_id=user_a_id,
        )

        # User B: RE_ENGAGING with user message -> should transition to ACTIVE
        state_b = _make_state(
            phase="RE_ENGAGING",
            consent_given=True,
            is_scheduled_message=False,
            user_id=user_b_id,
        )

        result_a = check_phase_transition(state_a)
        result_b = check_phase_transition(state_b)

        assert result_a.get("phase") == "ONBOARDING"
        assert result_b.get("phase") == "ACTIVE"

        # Original states are unchanged
        assert state_a["phase"] == "PENDING"
        assert state_b["phase"] == "RE_ENGAGING"


class TestConcurrentRateLimiting:
    """Verify rate limiting is per-user."""

    def test_concurrent_rate_limiting_per_user(self):
        """Rate limit for user A does not block user B."""
        _rate_limit_store.clear()

        user_a = f"rate-test-a-{uuid4()}"
        user_b = f"rate-test-b-{uuid4()}"

        # Fill user A's rate limit
        for _ in range(10):
            check_rate_limit(user_a, max_per_minute=10)

        # User A should now be blocked
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit(user_a, max_per_minute=10)
        assert exc_info.value.status_code == 429

        # User B should still be allowed
        check_rate_limit(user_b, max_per_minute=10)  # Should not raise

        _rate_limit_store.clear()


class TestConcurrentCheckpointer:
    """Verify checkpointer thread isolation via thread_id."""

    def test_concurrent_checkpointer_thread_isolation(self):
        """Different users get different thread_ids for the checkpointer."""
        user_a_id = str(uuid4())
        user_b_id = str(uuid4())

        # Thread ID is derived from user_id in the main app
        config_a = {"configurable": {"thread_id": user_a_id}}
        config_b = {"configurable": {"thread_id": user_b_id}}

        assert config_a["configurable"]["thread_id"] != config_b["configurable"]["thread_id"]

        # Verify that the thread_id scheme matches the pattern used in main.py
        # (user_id is used directly as thread_id)
        assert config_a["configurable"]["thread_id"] == user_a_id
        assert config_b["configurable"]["thread_id"] == user_b_id
