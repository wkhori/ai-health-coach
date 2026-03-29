"""Tests for the active phase subgraph."""

from unittest.mock import AsyncMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.graph.state import HealthCoachState
from src.graph.subgraphs.active import (
    _format_adherence,
    _format_goals,
    _format_milestones,
    active_agent,
    should_continue_active,
)


def _make_state(**overrides) -> HealthCoachState:
    base: HealthCoachState = {
        "messages": [HumanMessage(content="How am I doing?")],
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_id": "test-profile",
        "phase": "ACTIVE",
        "consent_given": True,
        "conversation_summary": "Patient has been walking 3x/week.",
        "turn_count": 5,
        "active_goals": [
            {
                "title": "Walk 30 mins",
                "description": "Walk 30 minutes daily",
                "confirmed": True,
                "milestones": [
                    {"title": "Week 1", "week_number": 1, "completed": True},
                    {"title": "Week 2", "week_number": 2, "completed": False},
                ],
            }
        ],
        "adherence_summary": {"adherence_rate": 75, "current_streak": 3},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
    }
    base.update(overrides)
    return base


class TestActiveAgent:
    """Tests for the active coaching agent."""

    @pytest.mark.asyncio
    async def test_returns_message_without_llm(self):
        """Without LLM, returns a default coaching message."""
        state = _make_state()
        result = await active_agent(state)
        assert "messages" in result
        assert isinstance(result["messages"][0], AIMessage)

    @pytest.mark.asyncio
    async def test_returns_response_text_without_llm(self):
        state = _make_state()
        result = await active_agent(state)
        assert "response_text" in result
        assert result["response_text"] != ""

    @pytest.mark.asyncio
    async def test_calls_llm_when_provided(self):
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Great job on your streak!")

        state = _make_state()
        result = await active_agent(state, llm=mock_llm)

        mock_llm.ainvoke.assert_called_once()
        assert "streak" in result["messages"][0].content.lower()

    @pytest.mark.asyncio
    async def test_includes_goals_in_system_prompt(self):
        """LLM is called with goals context in system prompt."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Hi!")

        state = _make_state()
        await active_agent(state, llm=mock_llm)

        call_args = mock_llm.ainvoke.call_args[0][0]
        system_content = call_args[0].content
        assert "Walk 30 mins" in system_content

    @pytest.mark.asyncio
    async def test_includes_adherence_in_system_prompt(self):
        """LLM is called with adherence data in system prompt."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Hi!")

        state = _make_state()
        await active_agent(state, llm=mock_llm)

        call_args = mock_llm.ainvoke.call_args[0][0]
        system_content = call_args[0].content
        assert "75%" in system_content

    @pytest.mark.asyncio
    async def test_handles_tool_calls(self):
        """Agent can return tool calls."""
        mock_response = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "set_reminder", "args": {"time": "9am"}}],
        )
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = mock_response

        state = _make_state()
        result = await active_agent(state, llm=mock_llm)
        assert result["messages"][0].tool_calls is not None

    @pytest.mark.asyncio
    async def test_handles_empty_goals(self):
        """Agent works with no active goals."""
        state = _make_state(active_goals=[])
        result = await active_agent(state)
        assert "messages" in result

    @pytest.mark.asyncio
    async def test_handles_empty_adherence(self):
        """Agent works with no adherence data."""
        state = _make_state(adherence_summary={})
        result = await active_agent(state)
        assert "messages" in result


class TestShouldContinueActive:
    """Tests for tool call continuation."""

    def test_continues_with_tool_calls(self):
        msg = AIMessage(
            content="",
            tool_calls=[{"id": "1", "name": "set_goal", "args": {}}],
        )
        state = _make_state(messages=[msg])
        assert should_continue_active(state) == "tools"

    def test_done_without_tool_calls(self):
        state = _make_state(messages=[AIMessage(content="Keep it up!")])
        assert should_continue_active(state) == "done"

    def test_done_with_empty_messages(self):
        state = _make_state(messages=[])
        assert should_continue_active(state) == "done"


class TestFormatHelpers:
    """Tests for prompt formatting helpers."""

    def test_format_goals_with_data(self):
        goals = [{"title": "Walk", "confirmed": True, "description": "Daily walk"}]
        result = _format_goals(goals)
        assert "Walk" in result
        assert "confirmed" in result

    def test_format_goals_empty(self):
        assert "No active goals" in _format_goals([])

    def test_format_adherence_with_data(self):
        result = _format_adherence({"adherence_rate": 80, "current_streak": 5})
        assert "80%" in result
        assert "5" in result

    def test_format_adherence_empty(self):
        assert "No adherence data" in _format_adherence({})

    def test_format_milestones_with_data(self):
        goals = [
            {
                "milestones": [
                    {"title": "Week 1", "week_number": 1, "completed": True},
                ]
            }
        ]
        result = _format_milestones(goals)
        assert "Week 1" in result
        assert "completed" in result

    def test_format_milestones_empty(self):
        assert "No milestones" in _format_milestones([])

    def test_format_milestones_no_milestones_key(self):
        """Goals without milestones key still work."""
        goals = [{"title": "Walk"}]
        result = _format_milestones(goals)
        assert "No milestones" in result
