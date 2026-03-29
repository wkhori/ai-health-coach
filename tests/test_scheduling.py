"""Tests for follow-up scheduling logic."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest

from src.scheduler.follow_up import process_due_reminders, schedule_follow_ups

TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")


@pytest.fixture
def mock_reminder_repo():
    repo = MagicMock()
    repo.create.return_value = {
        "id": str(uuid4()),
        "user_id": str(TEST_USER_ID),
        "reminder_type": "follow_up",
        "status": "pending",
    }
    repo.get_due_reminders.return_value = []
    repo.mark_sent.return_value = {"status": "sent"}
    repo.mark_failed.return_value = {"status": "failed"}
    return repo


class TestScheduleFollowUps:
    """Tests for scheduling re-engagement follow-ups."""

    def test_creates_three_reminders_by_default(self, mock_reminder_repo):
        result = schedule_follow_ups(
            user_id=TEST_USER_ID,
            reminder_repo=mock_reminder_repo,
        )
        assert len(result) == 3

    def test_uses_default_schedule_days_2_5_7(self, mock_reminder_repo):
        base = datetime(2024, 1, 1, 12, 0, 0)
        schedule_follow_ups(
            user_id=TEST_USER_ID,
            reminder_repo=mock_reminder_repo,
            base_time=base,
        )

        calls = mock_reminder_repo.create.call_args_list
        assert len(calls) == 3

        # Verify due_at values
        due_dates = [call.kwargs["due_at"] for call in calls]
        assert due_dates[0] == base + timedelta(days=2)
        assert due_dates[1] == base + timedelta(days=5)
        assert due_dates[2] == base + timedelta(days=7)

    def test_custom_schedule(self, mock_reminder_repo):
        result = schedule_follow_ups(
            user_id=TEST_USER_ID,
            reminder_repo=mock_reminder_repo,
            re_engage_days=[1, 3, 10],
        )
        assert len(result) == 3

    def test_attempt_numbers_are_sequential(self, mock_reminder_repo):
        schedule_follow_ups(
            user_id=TEST_USER_ID,
            reminder_repo=mock_reminder_repo,
        )

        calls = mock_reminder_repo.create.call_args_list
        attempt_numbers = [call.kwargs["attempt_number"] for call in calls]
        assert attempt_numbers == [1, 2, 3]

    def test_sets_correct_user_id(self, mock_reminder_repo):
        schedule_follow_ups(
            user_id=TEST_USER_ID,
            reminder_repo=mock_reminder_repo,
        )

        for call in mock_reminder_repo.create.call_args_list:
            assert call.kwargs["user_id"] == TEST_USER_ID


class TestProcessDueReminders:
    """Tests for processing due reminders."""

    @pytest.mark.asyncio
    async def test_processes_no_reminders(self, mock_reminder_repo):
        mock_reminder_repo.get_due_reminders.return_value = []
        results = await process_due_reminders(reminder_repo=mock_reminder_repo)
        assert results == []

    @pytest.mark.asyncio
    async def test_processes_due_reminder(self, mock_reminder_repo):
        reminder_id = str(uuid4())
        mock_reminder_repo.get_due_reminders.return_value = [
            {
                "id": reminder_id,
                "user_id": str(TEST_USER_ID),
                "reminder_type": "follow_up",
                "attempt_number": 1,
            }
        ]

        results = await process_due_reminders(reminder_repo=mock_reminder_repo)
        assert len(results) == 1
        assert results[0]["status"] == "sent"
        mock_reminder_repo.mark_sent.assert_called_once()

    @pytest.mark.asyncio
    async def test_marks_failed_on_error(self, mock_reminder_repo):
        reminder_id = str(uuid4())
        mock_reminder_repo.get_due_reminders.return_value = [
            {
                "id": reminder_id,
                "user_id": str(TEST_USER_ID),
                "reminder_type": "follow_up",
                "attempt_number": 1,
            }
        ]

        # Mock graph that raises an error
        mock_graph = AsyncMock()
        mock_graph.ainvoke.side_effect = Exception("LLM error")

        results = await process_due_reminders(
            reminder_repo=mock_reminder_repo,
            graph=mock_graph,
        )
        assert len(results) == 1
        assert results[0]["status"] == "failed"
        mock_reminder_repo.mark_failed.assert_called_once()

    @pytest.mark.asyncio
    async def test_invokes_graph_for_each_reminder(self, mock_reminder_repo):
        mock_reminder_repo.get_due_reminders.return_value = [
            {
                "id": str(uuid4()),
                "user_id": str(TEST_USER_ID),
                "reminder_type": "follow_up",
                "attempt_number": 1,
            },
            {
                "id": str(uuid4()),
                "user_id": str(TEST_USER_ID),
                "reminder_type": "follow_up",
                "attempt_number": 2,
            },
        ]

        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {"response_text": "Hi there!"}

        results = await process_due_reminders(
            reminder_repo=mock_reminder_repo,
            graph=mock_graph,
        )

        assert len(results) == 2
        assert mock_graph.ainvoke.call_count == 2

    @pytest.mark.asyncio
    async def test_processes_without_graph(self, mock_reminder_repo):
        """Can process reminders without a graph (just marks as sent)."""
        reminder_id = str(uuid4())
        mock_reminder_repo.get_due_reminders.return_value = [
            {
                "id": reminder_id,
                "user_id": str(TEST_USER_ID),
                "reminder_type": "follow_up",
                "attempt_number": 1,
            }
        ]

        results = await process_due_reminders(reminder_repo=mock_reminder_repo)
        assert len(results) == 1
        assert results[0]["status"] == "sent"
