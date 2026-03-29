"""Tests for the re-engagement subgraph."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.graph.state import HealthCoachState
from src.graph.subgraphs.re_engaging import (
    build_re_engage_context,
    re_engage_agent,
    should_continue_re_engage,
)


def _make_state(**overrides) -> HealthCoachState:
    base: HealthCoachState = {
        "messages": [],
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_id": "test-profile",
        "phase": "RE_ENGAGING",
        "consent_given": True,
        "conversation_summary": "Patient was walking 3x/week before going inactive.",
        "turn_count": 12,
        "active_goals": [{"title": "Walk 30 mins", "description": "Daily walking routine"}],
        "adherence_summary": {"adherence_rate": 60, "current_streak": 0},
        "safety_result": {},
        "is_scheduled_message": True,
        "scheduled_message_type": "1",
        "response_text": "",
    }
    base.update(overrides)
    return base


class TestBuildReEngageContext:
    """Tests for building re-engagement context."""

    def test_uses_state_goals_when_no_repo(self):
        state = _make_state()
        result = build_re_engage_context(state)
        assert len(result["active_goals"]) == 1

    def test_loads_goals_from_repo(self):
        mock_repo = MagicMock()
        mock_repo.get_active_goals.return_value = [
            {"title": "Stretch daily", "description": "Morning stretch"}
        ]

        state = _make_state()
        result = build_re_engage_context(state, goal_repo=mock_repo)
        assert len(result["active_goals"]) == 1
        assert result["active_goals"][0]["title"] == "Stretch daily"

    def test_handles_repo_error_gracefully(self):
        mock_repo = MagicMock()
        mock_repo.get_active_goals.side_effect = Exception("DB error")

        state = _make_state()
        # Should not raise, falls back to state goals
        result = build_re_engage_context(state, goal_repo=mock_repo)
        assert len(result["active_goals"]) == 1


class TestReEngageAgent:
    """Tests for the re-engagement agent."""

    @pytest.mark.asyncio
    async def test_returns_message_without_llm(self):
        state = _make_state()
        result = await re_engage_agent(state)
        assert "messages" in result
        assert isinstance(result["messages"][0], AIMessage)

    @pytest.mark.asyncio
    async def test_default_message_is_warm(self):
        """Default message uses no-guilt framing."""
        state = _make_state()
        result = await re_engage_agent(state)
        content = result["messages"][0].content.lower()
        assert "no pressure" in content or "hope" in content

    @pytest.mark.asyncio
    async def test_returns_response_text(self):
        state = _make_state()
        result = await re_engage_agent(state)
        assert result["response_text"] != ""

    @pytest.mark.asyncio
    async def test_calls_llm_when_provided(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="We miss you! Ready to get back?")

        state = _make_state()
        await re_engage_agent(state, llm=mock_llm)
        mock_llm.ainvoke.assert_called_once()

    @pytest.mark.asyncio
    async def test_includes_goals_in_system_prompt(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Hi!")

        state = _make_state()
        await re_engage_agent(state, llm=mock_llm)

        call_args = mock_llm.ainvoke.call_args[0][0]
        system_content = call_args[0].content
        assert "Walk 30 mins" in system_content

    @pytest.mark.asyncio
    async def test_includes_conversation_summary(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Hi!")

        state = _make_state()
        await re_engage_agent(state, llm=mock_llm)

        call_args = mock_llm.ainvoke.call_args[0][0]
        system_content = call_args[0].content
        assert "walking 3x/week" in system_content

    @pytest.mark.asyncio
    async def test_handles_tool_calls(self):
        mock_response = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "set_goal", "args": {"title": "New goal"}}],
        )
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        state = _make_state()
        result = await re_engage_agent(state, llm=mock_llm)
        assert result["messages"][0].tool_calls is not None


class TestShouldContinueReEngage:
    """Tests for tool call continuation."""

    def test_continues_with_tool_calls(self):
        msg = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "set_goal", "args": {}}],
        )
        state = _make_state(messages=[msg])
        assert should_continue_re_engage(state) == "tools"

    def test_done_without_tool_calls(self):
        state = _make_state(messages=[AIMessage(content="Welcome back!")])
        assert should_continue_re_engage(state) == "done"

    def test_done_with_empty_messages(self):
        state = _make_state(messages=[])
        assert should_continue_re_engage(state) == "done"

    def test_done_with_human_message(self):
        state = _make_state(messages=[HumanMessage(content="I'm back")])
        assert should_continue_re_engage(state) == "done"
