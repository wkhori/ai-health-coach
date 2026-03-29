"""Tests for the tool layer — tool definitions, goal decomposition, and tool invocation.

Minimum 18 tests required.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from tests.conftest import TEST_GOAL_ID, TEST_USER_ID


# ---------------------------------------------------------------------------
# GOAL DECOMPOSITION
# ---------------------------------------------------------------------------
class TestGoalDecomposition:
    def test_generates_four_milestones(self):
        from src.tools.goal_decomposition import generate_milestones

        milestones = generate_milestones(
            title="Run a 5K",
            description="Train to run a full 5K",
            frequency="daily",
            target_per_week=3,
        )
        assert len(milestones) == 4

    def test_milestones_have_required_fields(self):
        from src.tools.goal_decomposition import generate_milestones

        milestones = generate_milestones(
            title="Run a 5K",
            description="",
            frequency="daily",
            target_per_week=3,
        )
        for m in milestones:
            assert "title" in m
            assert "description" in m
            assert "week_number" in m
            assert isinstance(m["week_number"], int)

    def test_milestones_ordered_by_week(self):
        from src.tools.goal_decomposition import generate_milestones

        milestones = generate_milestones(
            title="Do yoga daily",
            description="Start a daily yoga practice",
            frequency="daily",
            target_per_week=5,
        )
        weeks = [m["week_number"] for m in milestones]
        assert weeks == [1, 2, 3, 4]

    def test_milestones_progressive(self):
        """Milestones should get progressively harder (week 4 title differs from week 1)."""
        from src.tools.goal_decomposition import generate_milestones

        milestones = generate_milestones(
            title="Run a 5K",
            description="",
            frequency="daily",
            target_per_week=3,
        )
        assert milestones[0]["title"] != milestones[3]["title"]

    def test_zero_target_per_week_handled(self):
        from src.tools.goal_decomposition import generate_milestones

        milestones = generate_milestones(
            title="Walk more",
            description="",
            frequency="",
            target_per_week=0,
        )
        assert len(milestones) == 4

    def test_empty_title_handled(self):
        from src.tools.goal_decomposition import generate_milestones

        milestones = generate_milestones(
            title="",
            description="",
            frequency="",
            target_per_week=3,
        )
        assert len(milestones) == 4


# ---------------------------------------------------------------------------
# TOOL DEFINITIONS — @tool decorator and signatures
# ---------------------------------------------------------------------------
class TestToolDecorators:
    def test_set_goal_is_tool(self):
        from src.tools.definitions import set_goal

        assert hasattr(set_goal, "name")
        assert set_goal.name == "set_goal"

    def test_set_reminder_is_tool(self):
        from src.tools.definitions import set_reminder

        assert hasattr(set_reminder, "name")
        assert set_reminder.name == "set_reminder"

    def test_get_program_summary_is_tool(self):
        from src.tools.definitions import get_program_summary

        assert hasattr(get_program_summary, "name")
        assert get_program_summary.name == "get_program_summary"

    def test_get_adherence_summary_is_tool(self):
        from src.tools.definitions import get_adherence_summary

        assert hasattr(get_adherence_summary, "name")
        assert get_adherence_summary.name == "get_adherence_summary"

    def test_alert_clinician_is_tool(self):
        from src.tools.definitions import alert_clinician

        assert hasattr(alert_clinician, "name")
        assert alert_clinician.name == "alert_clinician"

    def test_all_tools_have_docstrings(self):
        from src.tools.definitions import (
            alert_clinician,
            get_adherence_summary,
            get_program_summary,
            set_goal,
            set_reminder,
        )

        for tool in [
            set_goal,
            set_reminder,
            get_program_summary,
            get_adherence_summary,
            alert_clinician,
        ]:
            assert tool.description is not None
            assert len(tool.description) > 10


# ---------------------------------------------------------------------------
# TOOL INVOCATION — set_goal
# ---------------------------------------------------------------------------
class TestSetGoalTool:
    @patch("src.tools.definitions._get_goal_repo")
    @patch("src.tools.definitions._get_milestone_repo")
    def test_set_goal_creates_goal_and_milestones(self, mock_ms_repo_fn, mock_goal_repo_fn):
        from src.tools.definitions import set_goal

        mock_goal_repo = MagicMock()
        mock_goal_repo.create.return_value = {
            "id": str(TEST_GOAL_ID),
            "user_id": str(TEST_USER_ID),
            "title": "Run a 5K",
            "description": "Train to run 5K",
            "frequency": "daily",
            "target_per_week": 3,
        }
        mock_goal_repo_fn.return_value = mock_goal_repo

        mock_ms_repo = MagicMock()
        mock_ms_repo.create_batch.return_value = []
        mock_ms_repo_fn.return_value = mock_ms_repo

        result = set_goal.invoke(
            {
                "title": "Run a 5K",
                "description": "Train to run 5K",
                "frequency": "daily",
                "target_per_week": 3,
            }
        )

        mock_goal_repo.create.assert_called_once()
        mock_ms_repo.create_batch.assert_called_once()
        assert "Run a 5K" in result


# ---------------------------------------------------------------------------
# TOOL INVOCATION — set_reminder
# ---------------------------------------------------------------------------
class TestSetReminderTool:
    @patch("src.tools.definitions._get_reminder_repo")
    def test_set_reminder_creates_reminder(self, mock_repo_fn):
        from src.tools.definitions import set_reminder

        mock_repo = MagicMock()
        mock_repo.create.return_value = {
            "id": str(uuid4()),
            "user_id": str(TEST_USER_ID),
            "reminder_type": "custom",
            "message_template": "Time to stretch!",
            "status": "pending",
        }
        mock_repo_fn.return_value = mock_repo

        result = set_reminder.invoke(
            {
                "message": "Time to stretch!",
                "day_of_week": "Monday",
                "time_of_day": "09:00",
            }
        )

        mock_repo.create.assert_called_once()
        assert "reminder" in result.lower() or "Time to stretch" in result


# ---------------------------------------------------------------------------
# TOOL INVOCATION — get_program_summary
# ---------------------------------------------------------------------------
class TestGetProgramSummaryTool:
    def test_get_program_summary_returns_data(self):
        from src.tools.definitions import get_program_summary

        result = get_program_summary.invoke({"user_id": str(TEST_USER_ID)})
        assert isinstance(result, str)
        assert len(result) > 10  # Non-trivial response


# ---------------------------------------------------------------------------
# TOOL INVOCATION — get_adherence_summary
# ---------------------------------------------------------------------------
class TestGetAdherenceSummaryTool:
    def test_get_adherence_summary_returns_data(self):
        from src.tools.definitions import get_adherence_summary

        result = get_adherence_summary.invoke({"user_id": str(TEST_USER_ID)})
        assert isinstance(result, str)
        assert len(result) > 10


# ---------------------------------------------------------------------------
# TOOL INVOCATION — alert_clinician
# ---------------------------------------------------------------------------
class TestAlertClinicianTool:
    @patch("src.tools.definitions._get_alert_repo")
    def test_alert_clinician_creates_entry(self, mock_repo_fn):
        from src.tools.definitions import alert_clinician

        mock_repo = MagicMock()
        mock_repo.create.return_value = {
            "id": str(uuid4()),
            "user_id": str(TEST_USER_ID),
            "alert_type": "crisis",
            "urgency": "urgent",
            "status": "pending",
            "message": "Patient expressing distress",
        }
        mock_repo_fn.return_value = mock_repo

        result = alert_clinician.invoke(
            {
                "reason": "Patient expressing distress",
                "urgency": "urgent",
            }
        )

        mock_repo.create.assert_called_once()
        assert "alert" in result.lower() or "clinician" in result.lower()

    @patch("src.tools.definitions._get_alert_repo")
    def test_alert_clinician_routine_urgency(self, mock_repo_fn):
        from src.tools.definitions import alert_clinician

        mock_repo = MagicMock()
        mock_repo.create.return_value = {
            "id": str(uuid4()),
            "user_id": str(TEST_USER_ID),
            "alert_type": "clinical_boundary",
            "urgency": "routine",
            "status": "pending",
            "message": "Repeated clinical questions",
        }
        mock_repo_fn.return_value = mock_repo

        result = alert_clinician.invoke(
            {
                "reason": "Repeated clinical questions",
                "urgency": "routine",
            }
        )

        assert isinstance(result, str)
