import json
import sqlite3
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from src.models.enums import AlertUrgency, PhaseState, SafetyAction, SafetyClassificationType


def _row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    """Convert a sqlite3.Row to a plain dict, deserializing JSON and boolean columns."""
    if row is None:
        return None
    d = dict(row)
    # Convert JSON string columns
    for key in ("tool_calls", "tool_results", "categories", "flagged_phrases"):
        if key in d and isinstance(d[key], str):
            d[key] = json.loads(d[key])
    # Convert boolean columns
    for key in ("confirmed", "completed"):
        if key in d:
            d[key] = bool(d[key])
    return d


def _rows_to_list(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    """Convert a list of sqlite3.Row objects to a list of dicts."""
    return [_row_to_dict(r) for r in rows]  # type: ignore[misc]


class ProfileRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def get_by_user_id(self, user_id: UUID) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE user_id = ?", (str(user_id),)
        ).fetchone()
        return _row_to_dict(row)

    def update_phase(self, profile_id: UUID, phase: PhaseState) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE profiles SET phase = ?, phase_updated_at = ? WHERE id = ?",
            (phase.value, now, str(profile_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (str(profile_id),)
        ).fetchone()
        return _row_to_dict(row)

    def update_consent(self, profile_id: UUID, consent_version: str) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE profiles SET consent_given_at = ?, consent_version = ?, consent_revoked_at = NULL WHERE id = ?",
            (now, consent_version, str(profile_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (str(profile_id),)
        ).fetchone()
        return _row_to_dict(row)

    def revoke_consent(self, profile_id: UUID) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE profiles SET consent_revoked_at = ? WHERE id = ?",
            (now, str(profile_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (str(profile_id),)
        ).fetchone()
        return _row_to_dict(row)

    def get_all(self) -> list[dict[str, Any]]:
        """Return all profiles ordered by display name."""
        rows = self.conn.execute(
            "SELECT * FROM profiles ORDER BY display_name"
        ).fetchall()
        return _rows_to_list(rows)

    def update_last_message(self, profile_id: UUID) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE profiles SET last_message_at = ? WHERE id = ?",
            (now, str(profile_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM profiles WHERE id = ?", (str(profile_id),)
        ).fetchone()
        return _row_to_dict(row)


class GoalRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def _attach_milestones(self, goals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """For each goal dict, query and attach its milestones list."""
        for goal in goals:
            milestone_rows = self.conn.execute(
                "SELECT * FROM milestones WHERE goal_id = ? ORDER BY week_number",
                (goal["id"],),
            ).fetchall()
            goal["milestones"] = _rows_to_list(milestone_rows)
        return goals

    def create(
        self,
        user_id: UUID,
        title: str,
        description: str = "",
        frequency: str = "",
        target_per_week: int = 0,
    ) -> dict[str, Any]:
        goal_id = str(uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO goals (id, user_id, title, description, frequency, target_per_week, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (goal_id, str(user_id), title, description, frequency, target_per_week, now, now),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM goals WHERE id = ?", (goal_id,)).fetchone()
        return _row_to_dict(row)  # type: ignore[return-value]

    def get_by_user(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC",
            (str(user_id),),
        ).fetchall()
        goals = _rows_to_list(rows)
        return self._attach_milestones(goals)

    def get_active_goals(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM goals WHERE user_id = ? AND status = 'active' ORDER BY created_at DESC",
            (str(user_id),),
        ).fetchall()
        goals = _rows_to_list(rows)
        return self._attach_milestones(goals)

    def get_confirmed_goals(self, user_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM goals WHERE user_id = ? AND confirmed = 1 AND status = 'active' ORDER BY created_at DESC",
            (str(user_id),),
        ).fetchall()
        goals = _rows_to_list(rows)
        return self._attach_milestones(goals)

    def confirm_goal(self, goal_id: UUID) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE goals SET confirmed = 1, updated_at = ? WHERE id = ?",
            (now, str(goal_id)),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM goals WHERE id = ?", (str(goal_id),)).fetchone()
        return _row_to_dict(row)


class MilestoneRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create_batch(
        self, goal_id: UUID, user_id: UUID, milestones: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        created_ids: list[str] = []
        now = datetime.now().isoformat()
        for m in milestones:
            milestone_id = str(uuid4())
            self.conn.execute(
                """INSERT INTO milestones (id, goal_id, user_id, title, description, week_number, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    milestone_id,
                    str(goal_id),
                    str(user_id),
                    m["title"],
                    m.get("description", ""),
                    m["week_number"],
                    now,
                ),
            )
            created_ids.append(milestone_id)
        self.conn.commit()
        results: list[dict[str, Any]] = []
        for mid in created_ids:
            row = self.conn.execute("SELECT * FROM milestones WHERE id = ?", (mid,)).fetchone()
            d = _row_to_dict(row)
            if d is not None:
                results.append(d)
        return results

    def get_by_goal(self, goal_id: UUID) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM milestones WHERE goal_id = ? ORDER BY week_number",
            (str(goal_id),),
        ).fetchall()
        return _rows_to_list(rows)

    def mark_completed(self, milestone_id: UUID) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE milestones SET completed = 1, completed_at = ? WHERE id = ?",
            (now, str(milestone_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM milestones WHERE id = ?", (str(milestone_id),)
        ).fetchone()
        return _row_to_dict(row)


class ReminderRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        user_id: UUID,
        reminder_type: str,
        due_at: datetime,
        message_template: str = "",
        attempt_number: int = 1,
    ) -> dict[str, Any]:
        reminder_id = str(uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO reminders (id, user_id, reminder_type, due_at, message_template, attempt_number, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                reminder_id,
                str(user_id),
                reminder_type,
                due_at.isoformat(),
                message_template,
                attempt_number,
                now,
            ),
        )
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM reminders WHERE id = ?", (reminder_id,)).fetchone()
        return _row_to_dict(row)  # type: ignore[return-value]

    def get_due_reminders(self) -> list[dict[str, Any]]:
        now = datetime.now().isoformat()
        rows = self.conn.execute(
            "SELECT * FROM reminders WHERE status = 'pending' AND due_at <= ? ORDER BY due_at",
            (now,),
        ).fetchall()
        return _rows_to_list(rows)

    def mark_sent(self, reminder_id: UUID) -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE reminders SET status = 'sent', sent_at = ? WHERE id = ?",
            (now, str(reminder_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (str(reminder_id),)
        ).fetchone()
        return _row_to_dict(row)

    def mark_failed(self, reminder_id: UUID) -> dict[str, Any] | None:
        self.conn.execute(
            "UPDATE reminders SET status = 'failed' WHERE id = ?",
            (str(reminder_id),),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM reminders WHERE id = ?", (str(reminder_id),)
        ).fetchone()
        return _row_to_dict(row)

    def get_attempt_count(self, user_id: UUID) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM reminders WHERE user_id = ? AND reminder_type = 'follow_up' AND status = 'sent'",
            (str(user_id),),
        ).fetchone()
        return row[0] if row else 0


class ConversationRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def add_turn(
        self,
        user_id: UUID,
        role: str,
        content: str,
        phase: str,
        turn_number: int,
        tool_calls: dict | None = None,
        tool_results: dict | None = None,
        token_count_input: int | None = None,
        token_count_output: int | None = None,
    ) -> dict[str, Any]:
        turn_id = str(uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO conversation_turns
               (id, user_id, role, content, phase, turn_number, tool_calls, tool_results,
                token_count_input, token_count_output, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                turn_id,
                str(user_id),
                role,
                content,
                phase,
                turn_number,
                json.dumps(tool_calls) if tool_calls is not None else None,
                json.dumps(tool_results) if tool_results is not None else None,
                token_count_input,
                token_count_output,
                now,
            ),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM conversation_turns WHERE id = ?", (turn_id,)
        ).fetchone()
        return _row_to_dict(row)  # type: ignore[return-value]

    def get_recent_turns(self, user_id: UUID, limit: int = 10) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM conversation_turns WHERE user_id = ? ORDER BY turn_number DESC LIMIT ?",
            (str(user_id), limit),
        ).fetchall()
        data = _rows_to_list(rows)
        data.reverse()
        return data

    def get_turn_count(self, user_id: UUID) -> int:
        row = self.conn.execute(
            "SELECT COUNT(*) FROM conversation_turns WHERE user_id = ?",
            (str(user_id),),
        ).fetchone()
        return row[0] if row else 0


class SafetyAuditRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def log_entry(
        self,
        user_id: UUID,
        input_text: str,
        classification: SafetyClassificationType,
        confidence: float,
        action_taken: SafetyAction,
        tier: str = "llm",
        categories: list[str] | None = None,
        flagged_phrases: list[str] | None = None,
        reasoning: str = "",
        model_used: str = "",
        conversation_turn_id: UUID | None = None,
    ) -> dict[str, Any]:
        entry_id = str(uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO safety_audit_log
               (id, user_id, input_text, classification, confidence, action_taken, tier,
                categories, flagged_phrases, reasoning, model_used, conversation_turn_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                entry_id,
                str(user_id),
                input_text,
                classification.value,
                confidence,
                action_taken.value,
                tier,
                json.dumps(categories or []),
                json.dumps(flagged_phrases or []),
                reasoning,
                model_used,
                str(conversation_turn_id) if conversation_turn_id else None,
                now,
            ),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM safety_audit_log WHERE id = ?", (entry_id,)
        ).fetchone()
        return _row_to_dict(row)  # type: ignore[return-value]

    def get_recent_entries(self, user_id: UUID, limit: int = 20) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM safety_audit_log WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (str(user_id), limit),
        ).fetchall()
        return _rows_to_list(rows)


class SummaryRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        user_id: UUID,
        summary_text: str,
        turns_covered_from: int,
        turns_covered_to: int,
    ) -> dict[str, Any]:
        summary_id = str(uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO conversation_summaries
               (id, user_id, summary_text, turns_covered_from, turns_covered_to, created_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (summary_id, str(user_id), summary_text, turns_covered_from, turns_covered_to, now),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM conversation_summaries WHERE id = ?", (summary_id,)
        ).fetchone()
        return _row_to_dict(row)  # type: ignore[return-value]

    def get_latest(self, user_id: UUID) -> dict[str, Any] | None:
        row = self.conn.execute(
            "SELECT * FROM conversation_summaries WHERE user_id = ? ORDER BY created_at DESC LIMIT 1",
            (str(user_id),),
        ).fetchone()
        return _row_to_dict(row)


class AlertRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def create(
        self,
        user_id: UUID,
        alert_type: str,
        urgency: AlertUrgency = AlertUrgency.ROUTINE,
        message: str = "",
        safety_audit_id: UUID | None = None,
    ) -> dict[str, Any]:
        alert_id = str(uuid4())
        now = datetime.now().isoformat()
        self.conn.execute(
            """INSERT INTO clinician_alerts
               (id, user_id, alert_type, urgency, message, safety_audit_id, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                alert_id,
                str(user_id),
                alert_type,
                urgency.value,
                message,
                str(safety_audit_id) if safety_audit_id else None,
                now,
            ),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM clinician_alerts WHERE id = ?", (alert_id,)
        ).fetchone()
        return _row_to_dict(row)  # type: ignore[return-value]

    def get_unacknowledged(self) -> list[dict[str, Any]]:
        rows = self.conn.execute(
            "SELECT * FROM clinician_alerts WHERE status = 'pending' ORDER BY created_at DESC"
        ).fetchall()
        return _rows_to_list(rows)

    def get_unacknowledged_with_patient(self) -> list[dict[str, Any]]:
        """Return unacknowledged alerts joined with patient display_name."""
        rows = self.conn.execute(
            """SELECT ca.*, p.display_name as patient_name
               FROM clinician_alerts ca
               LEFT JOIN profiles p ON ca.user_id = p.user_id
               WHERE ca.status = 'pending'
               ORDER BY ca.created_at DESC"""
        ).fetchall()
        return _rows_to_list(rows)

    def count_by_user(self, user_id: UUID) -> int:
        """Count unacknowledged alerts for a specific user."""
        row = self.conn.execute(
            "SELECT COUNT(*) FROM clinician_alerts WHERE user_id = ? AND status = 'pending'",
            (str(user_id),),
        ).fetchone()
        return row[0] if row else 0

    def acknowledge(self, alert_id: UUID, notes: str = "") -> dict[str, Any] | None:
        now = datetime.now().isoformat()
        self.conn.execute(
            "UPDATE clinician_alerts SET status = 'acknowledged', acknowledged_at = ?, notes = ? WHERE id = ?",
            (now, notes, str(alert_id)),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT * FROM clinician_alerts WHERE id = ?", (str(alert_id),)
        ).fetchone()
        return _row_to_dict(row)
