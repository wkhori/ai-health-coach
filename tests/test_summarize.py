"""Tests for conversation summarization logic."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from src.graph.nodes.summarize import should_summarize, summarize_conversation
from src.graph.state import HealthCoachState


def _make_state(**overrides) -> HealthCoachState:
    base: HealthCoachState = {
        "messages": [
            HumanMessage(content="How do I start?"),
            AIMessage(content="Let's set a goal!"),
            HumanMessage(content="I want to walk daily."),
            AIMessage(content="Great choice!"),
            HumanMessage(content="3 times a week."),
            AIMessage(content="Perfect, I've saved that."),
        ],
        "user_id": "00000000-0000-0000-0000-000000000001",
        "profile_id": "test-profile",
        "phase": "ACTIVE",
        "consent_given": True,
        "conversation_summary": "",
        "turn_count": 6,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
    }
    base.update(overrides)
    return base


class TestShouldSummarize:
    """Tests for summarization trigger logic."""

    def test_summarize_at_turn_6(self):
        state = _make_state(turn_count=6)
        assert should_summarize(state, every_n=6) is True

    def test_summarize_at_turn_12(self):
        state = _make_state(turn_count=12)
        assert should_summarize(state, every_n=6) is True

    def test_no_summarize_at_turn_5(self):
        state = _make_state(turn_count=5)
        assert should_summarize(state, every_n=6) is False

    def test_no_summarize_at_turn_0(self):
        state = _make_state(turn_count=0)
        assert should_summarize(state, every_n=6) is False

    def test_no_summarize_at_turn_1(self):
        state = _make_state(turn_count=1)
        assert should_summarize(state, every_n=6) is False


class TestSummarizeConversation:
    """Tests for conversation summarization."""

    @pytest.mark.asyncio
    async def test_returns_empty_when_not_needed(self):
        """Skips summarization when turn count is not a multiple of N."""
        state = _make_state(turn_count=5)
        result = await summarize_conversation(state, every_n=6)
        assert result == {}

    @pytest.mark.asyncio
    async def test_returns_empty_without_llm(self):
        """Skips summarization when no LLM is provided."""
        state = _make_state(turn_count=6)
        result = await summarize_conversation(state, every_n=6)
        assert result == {}

    @pytest.mark.asyncio
    async def test_generates_summary_with_llm(self):
        """Generates summary using the provided LLM."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(
            content="Patient wants to walk 3x/week. Goal set."
        )

        state = _make_state(turn_count=6)
        result = await summarize_conversation(state, llm=mock_llm, every_n=6)

        assert "conversation_summary" in result
        assert "walk" in result["conversation_summary"].lower()

    @pytest.mark.asyncio
    async def test_calls_llm_with_system_prompt(self):
        """LLM receives a system prompt about summarization."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Summary here.")

        state = _make_state(turn_count=6)
        await summarize_conversation(state, llm=mock_llm, every_n=6)

        call_args = mock_llm.ainvoke.call_args[0][0]
        assert call_args[0].type == "system"
        assert "summarize" in call_args[0].content.lower()

    @pytest.mark.asyncio
    async def test_persists_summary_to_repo(self):
        """Summary is saved via summary_repo."""
        mock_llm = AsyncMock()
        mock_llm.ainvoke.return_value = AIMessage(content="Summary.")
        mock_repo = MagicMock()

        state = _make_state(turn_count=6)
        await summarize_conversation(state, llm=mock_llm, summary_repo=mock_repo, every_n=6)

        mock_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_empty_messages(self):
        """Returns empty when no messages to summarize."""
        state = _make_state(turn_count=6, messages=[])
        mock_llm = AsyncMock()
        result = await summarize_conversation(state, llm=mock_llm, every_n=6)
        assert result == {}
