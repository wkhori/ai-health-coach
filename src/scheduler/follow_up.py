"""Follow-up scheduling logic for re-engagement."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from uuid import UUID


async def process_due_reminders(
    *,
    reminder_repo: Any,
    graph: Any = None,
    config_factory: Any = None,
) -> list[dict]:
    """Query due reminders and process each one through the graph.

    Returns a list of processed reminder results.
    """
    due_reminders = reminder_repo.get_due_reminders()
    results = []

    for reminder in due_reminders:
        user_id = reminder.get("user_id", "")
        reminder_id = reminder.get("id", "")
        attempt = reminder.get("attempt_number", 1)

        try:
            if graph:
                # Build graph input for scheduled message
                graph_input = {
                    "messages": [],
                    "user_id": user_id,
                    "profile_id": "",
                    "phase": "RE_ENGAGING",
                    "consent_given": True,
                    "conversation_summary": "",
                    "turn_count": 0,
                    "active_goals": [],
                    "adherence_summary": {},
                    "safety_result": {},
                    "is_scheduled_message": True,
                    "scheduled_message_type": str(attempt),
                    "response_text": "",
                }

                config = {"configurable": {"thread_id": user_id}}
                if config_factory:
                    config = config_factory(user_id)

                await graph.ainvoke(graph_input, config)

            # Mark reminder as sent
            reminder_repo.mark_sent(
                UUID(reminder_id) if isinstance(reminder_id, str) else reminder_id
            )
            results.append({"reminder_id": reminder_id, "status": "sent"})

        except Exception as e:
            # Mark as failed
            reminder_repo.mark_failed(
                UUID(reminder_id) if isinstance(reminder_id, str) else reminder_id
            )
            results.append({"reminder_id": reminder_id, "status": "failed", "error": str(e)})

    return results


def schedule_follow_ups(
    *,
    user_id: UUID,
    reminder_repo: Any,
    re_engage_days: list[int] | None = None,
    base_time: datetime | None = None,
) -> list[dict]:
    """Create Day 2, 5, 7 reminders based on re_engage_schedule config.

    Args:
        user_id: The patient's user ID
        reminder_repo: ReminderRepository instance
        re_engage_days: List of days for re-engagement (default: [2, 5, 7])
        base_time: Base time to calculate from (default: now)

    Returns:
        List of created reminder records
    """
    if re_engage_days is None:
        re_engage_days = [2, 5, 7]

    if base_time is None:
        base_time = datetime.now()

    created = []
    for i, day in enumerate(re_engage_days):
        due_at = base_time + timedelta(days=day)
        attempt_number = i + 1

        reminder = reminder_repo.create(
            user_id=user_id,
            reminder_type="follow_up",
            due_at=due_at,
            message_template=f"Re-engagement attempt {attempt_number}",
            attempt_number=attempt_number,
        )
        created.append(reminder)

    return created
