"""Tests for the onboarding subgraph."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.graph.state import HealthCoachState
from src.graph.subgraphs.onboarding import (
    check_onboarding_complete,
    onboard_agent,
    should_continue_onboarding,
)


def _make_state(**overrides) -> HealthCoachState:
    base: HealthCoachState = {
        "messages": [HumanMessage(content="hello")],
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_id": "test-profile",
        "phase": "ONBOARDING",
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


class TestOnboardAgent:
    """Tests for the onboarding agent node."""

    @pytest.mark.asyncio
    async def test_returns_welcome_without_llm(self):
        """Without LLM, returns a default welcome message."""
        state = _make_state()
        result = await onboard_agent(state)
        assert "messages" in result
        assert isinstance(result["messages"][0], AIMessage)
        assert "goal" in result["messages"][0].content.lower()

    @pytest.mark.asyncio
    async def test_returns_response_text_without_llm(self):
        """Without LLM, response_text is set."""
        state = _make_state()
        result = await onboard_agent(state)
        assert "response_text" in result
        assert result["response_text"] != ""

    @pytest.mark.asyncio
    async def test_calls_llm_when_provided(self):
        """When LLM is provided, it gets invoked."""
        mock_llm = AsyncMock()
        mock_response = AIMessage(content="Welcome! Let's set your first goal.")
        mock_llm.ainvoke.return_value = mock_response

        state = _make_state()
        result = await onboard_agent(state, llm=mock_llm)

        mock_llm.ainvoke.assert_called_once()
        assert result["messages"][0].content == "Welcome! Let's set your first goal."

    @pytest.mark.asyncio
    async def test_includes_system_prompt(self):
        """LLM is called with system prompt prepended."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Hi!")

        state = _make_state()
        await onboard_agent(state, llm=mock_llm)

        call_args = mock_llm.ainvoke.call_args[0][0]
        # First message should be system message
        assert call_args[0].type == "system"
        assert "wellness coach" in call_args[0].content.lower()

    @pytest.mark.asyncio
    async def test_handles_tool_call_response(self):
        """When LLM returns tool calls, they are included in messages."""
        mock_response = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "set_goal", "args": {"title": "Walk"}}],
        )
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        state = _make_state()
        result = await onboard_agent(state, llm=mock_llm)

        assert result["messages"][0].tool_calls is not None
        assert len(result["messages"][0].tool_calls) == 1


class TestCheckOnboardingComplete:
    """Tests for onboarding completion check."""

    def test_complete_with_confirmed_goal(self):
        """Sets phase to ACTIVE when confirmed goal exists."""
        state = _make_state(active_goals=[{"title": "Walk daily", "confirmed": True}])
        result = check_onboarding_complete(state)
        assert result.get("phase") == "ACTIVE"

    def test_incomplete_without_confirmed_goal(self):
        """Returns empty when no confirmed goal."""
        state = _make_state(active_goals=[{"title": "Walk daily", "confirmed": False}])
        result = check_onboarding_complete(state)
        assert result == {}

    def test_incomplete_with_empty_goals(self):
        """Returns empty when no goals at all."""
        state = _make_state(active_goals=[])
        result = check_onboarding_complete(state)
        assert result == {}


class TestShouldContinueOnboarding:
    """Tests for tool call continuation check."""

    def test_continues_with_tool_calls(self):
        """Returns 'tools' when last message has tool calls."""
        msg = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "set_goal", "args": {}}],
        )
        state = _make_state(messages=[msg])
        assert should_continue_onboarding(state) == "tools"

    def test_done_without_tool_calls(self):
        """Returns 'done' when last message has no tool calls."""
        state = _make_state(messages=[AIMessage(content="Welcome!")])
        assert should_continue_onboarding(state) == "done"

    def test_done_with_empty_messages(self):
        """Returns 'done' when no messages."""
        state = _make_state(messages=[])
        assert should_continue_onboarding(state) == "done"
