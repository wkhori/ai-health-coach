"""Tool definitions for the AI Health Coach — 5 tools using @tool decorator.

Tools are bound per-phase via ChatAnthropic.bind_tools().
"""

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

import structlog
from langchain_core.tools import tool

from src.models.enums import AlertUrgency
from src.tools.goal_decomposition import generate_milestones

logger = structlog.get_logger(__name__)

# Default user_id for tool operations (set at runtime by the graph)
_CURRENT_USER_ID: str = "00000000-0000-0000-0000-000000000001"

# Days of the week mapping for reminder scheduling
_DAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


# ---------------------------------------------------------------------------
# Repository accessors (mockable for tests)
# ---------------------------------------------------------------------------
def _get_goal_repo() -> Any:
    """Get a GoalRepository instance. Separated for testability."""
    from src.config import get_settings
    from src.db.client import get_db
    from src.db.repositories import GoalRepository

    settings = get_settings()
    conn = get_db(settings.database_path)
    return GoalRepository(conn)


def _get_milestone_repo() -> Any:
    """Get a MilestoneRepository instance. Separated for testability."""
    from src.config import get_settings
    from src.db.client import get_db
    from src.db.repositories import MilestoneRepository

    settings = get_settings()
    conn = get_db(settings.database_path)
    return MilestoneRepository(conn)


def _get_reminder_repo() -> Any:
    """Get a ReminderRepository instance. Separated for testability."""
    from src.config import get_settings
    from src.db.client import get_db
    from src.db.repositories import ReminderRepository

    settings = get_settings()
    conn = get_db(settings.database_path)
    return ReminderRepository(conn)


def _get_alert_repo() -> Any:
    """Get an AlertRepository instance. Separated for testability."""
    from src.config import get_settings
    from src.db.client import get_db
    from src.db.repositories import AlertRepository

    settings = get_settings()
    conn = get_db(settings.database_path)
    return AlertRepository(conn)


# ---------------------------------------------------------------------------
# Tool 1: set_goal
# ---------------------------------------------------------------------------
@tool
def set_goal(
    title: str,
    description: str,
    frequency: str,
    target_per_week: int,
) -> str:
    """Create a new wellness goal for the patient and generate a 4-week milestone plan.

    Use this tool when the patient wants to set a new exercise or wellness goal.
    The tool automatically creates progressive weekly milestones to help them
    build up to their target gradually.

    Args:
        title: Short name for the goal (e.g., "Run a 5K", "Daily yoga")
        description: Detailed description of what the patient wants to achieve
        frequency: How often they plan to work on this (e.g., "daily", "3 times per week")
        target_per_week: Number of sessions they want to complete per week
    """
    goal_repo = _get_goal_repo()
    ms_repo = _get_milestone_repo()

    # Create the goal
    goal_data = goal_repo.create(
        user_id=UUID(_CURRENT_USER_ID),
        title=title,
        description=description,
        frequency=frequency,
        target_per_week=target_per_week,
    )
    goal_id = UUID(goal_data["id"])

    # Generate milestones
    milestones = generate_milestones(
        title=title,
        description=description,
        frequency=frequency,
        target_per_week=target_per_week,
    )

    # Save milestones to DB
    ms_repo.create_batch(
        goal_id=goal_id,
        user_id=UUID(_CURRENT_USER_ID),
        milestones=milestones,
    )

    logger.info("goal_created", goal_id=str(goal_id), title=title)

    # Build response
    milestone_summary = "\n".join(f"  - {m['title']}" for m in milestones)
    return (
        f"Goal '{title}' has been set! Here's your 4-week plan:\n"
        f"{milestone_summary}\n\n"
        f"I'll help you track your progress each week."
    )


# ---------------------------------------------------------------------------
# Tool 2: set_reminder
# ---------------------------------------------------------------------------
@tool
def set_reminder(
    message: str,
    day_of_week: str,
    time_of_day: str,
) -> str:
    """Create a reminder for the patient on a specific day and time.

    Use this tool when the patient wants to be reminded about their exercises,
    goals, or any wellness-related activity.

    Args:
        message: The reminder message to send (e.g., "Time for your morning stretches!")
        day_of_week: Day of the week (e.g., "Monday", "Wednesday", "Friday")
        time_of_day: Time in HH:MM format (e.g., "09:00", "18:30")
    """
    reminder_repo = _get_reminder_repo()

    # Calculate the next occurrence of the specified day
    now = datetime.now()
    target_day = _DAY_MAP.get(day_of_week.lower(), 0)
    days_ahead = target_day - now.weekday()
    if days_ahead <= 0:
        days_ahead += 7

    # Parse time
    try:
        hour, minute = (int(x) for x in time_of_day.split(":"))
    except (ValueError, AttributeError):
        hour, minute = 9, 0

    due_at = now + timedelta(days=days_ahead)
    due_at = due_at.replace(hour=hour, minute=minute, second=0, microsecond=0)

    reminder_repo.create(
        user_id=UUID(_CURRENT_USER_ID),
        reminder_type="custom",
        due_at=due_at,
        message_template=message,
    )

    logger.info("reminder_set", day=day_of_week, time=time_of_day, message=message)

    return (
        f'Reminder set for {day_of_week} at {time_of_day}: "{message}". '
        f"I'll make sure you get reminded!"
    )


# ---------------------------------------------------------------------------
# Tool 3: get_program_summary
# ---------------------------------------------------------------------------
@tool
def get_program_summary(user_id: str) -> str:
    """Get a summary of the patient's assigned exercise program.

    Use this tool when the patient asks about their current exercises,
    what they should be doing, or wants an overview of their program.

    Args:
        user_id: The patient's user ID
    """
    # Stub: return realistic sample data per the brief
    logger.info("program_summary_requested", user_id=user_id)

    return (
        "Here's your current exercise program:\n\n"
        "1. **Upper Body Strengthening** — Resistance band exercises, 3x/week\n"
        "   - Bicep curls: 3 sets of 12\n"
        "   - Shoulder press: 3 sets of 10\n"
        "   - Rows: 3 sets of 12\n\n"
        "2. **Lower Body Mobility** — Stretching routine, daily\n"
        "   - Hamstring stretch: 30 seconds each side\n"
        "   - Quad stretch: 30 seconds each side\n"
        "   - Hip flexor stretch: 30 seconds each side\n\n"
        "3. **Cardio** — Walking program, 4x/week\n"
        "   - Brisk walking: 20-30 minutes\n"
        "   - Target heart rate: moderate intensity"
    )


# ---------------------------------------------------------------------------
# Tool 4: get_adherence_summary
# ---------------------------------------------------------------------------
@tool
def get_adherence_summary(user_id: str) -> str:
    """Get the patient's exercise adherence statistics including streak and completion rate.

    Use this tool when the patient asks about their progress, streak,
    how well they've been doing, or wants motivation based on their track record.

    Args:
        user_id: The patient's user ID
    """
    # Stub: return realistic sample data per the brief
    logger.info("adherence_summary_requested", user_id=user_id)

    return (
        "Here's your adherence summary:\n\n"
        "- Current streak: 5 days\n"
        "- This week: 4/5 sessions completed (80%)\n"
        "- Last week: 3/5 sessions completed (60%)\n"
        "- Trend: Improving! Up 20% from last week.\n"
        "- Total sessions this month: 15\n\n"
        "You're building great momentum. Keep it up!"
    )


# ---------------------------------------------------------------------------
# Tool 5: alert_clinician
# ---------------------------------------------------------------------------
@tool
def alert_clinician(reason: str, urgency: str) -> str:
    """Create an alert for the patient's clinician or care team.

    Use this tool when the patient's message indicates they may need
    clinical attention, or when a safety concern is detected.

    Args:
        reason: Description of why the clinician is being alerted
        urgency: Alert urgency level — "routine" or "urgent"
    """
    alert_repo = _get_alert_repo()

    urgency_enum = AlertUrgency.URGENT if urgency.lower() == "urgent" else AlertUrgency.ROUTINE
    alert_type = "crisis" if urgency_enum == AlertUrgency.URGENT else "clinical_boundary"

    alert_repo.create(
        user_id=UUID(_CURRENT_USER_ID),
        alert_type=alert_type,
        urgency=urgency_enum,
        message=reason,
    )

    logger.warning(
        "clinician_alerted",
        reason=reason,
        urgency=urgency,
        alert_type=alert_type,
    )

    return f"Clinician alert created ({urgency}): {reason}. Your care team has been notified."
