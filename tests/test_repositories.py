"""Comprehensive integration tests for all 8 SQLite repository classes."""

import sqlite3
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from src.db.repositories import (
    AlertRepository,
    ConversationRepository,
    GoalRepository,
    MilestoneRepository,
    ProfileRepository,
    ReminderRepository,
    SafetyAuditRepository,
    SummaryRepository,
)
from src.models.enums import (
    AlertUrgency,
    PhaseState,
    SafetyAction,
    SafetyClassificationType,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _seed_user(conn: sqlite3.Connection, user_id: UUID | None = None) -> str:
    """Insert a minimal user row and return the user_id string."""
    uid = str(user_id or uuid4())
    conn.execute(
        "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
        (uid, f"{uid}@test.com", "hash"),
    )
    conn.commit()
    return uid


def _seed_profile(
    conn: sqlite3.Connection, user_id: str, phase: str = "PENDING"
) -> str:
    """Insert a profile for *user_id* and return the profile id string."""
    profile_id = str(uuid4())
    now = datetime.now().isoformat()
    conn.execute(
        """INSERT INTO profiles (id, user_id, display_name, phase, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (profile_id, user_id, "Test User", phase, now, now),
    )
    conn.commit()
    return profile_id


# ---------------------------------------------------------------------------
# ProfileRepository
# ---------------------------------------------------------------------------


class TestProfileRepository:
    """Tests for ProfileRepository (8 methods exercised across 10 tests)."""

    def test_get_by_user_id_returns_profile(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid)
        repo = ProfileRepository(db_conn)

        result = repo.get_by_user_id(UUID(uid))

        assert result is not None
        assert result["id"] == pid
        assert result["user_id"] == uid
        assert result["phase"] == "PENDING"

    def test_get_by_user_id_not_found(self, db_conn: sqlite3.Connection) -> None:
        repo = ProfileRepository(db_conn)
        result = repo.get_by_user_id(uuid4())
        assert result is None

    def test_update_phase_changes_phase(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid, phase="PENDING")
        repo = ProfileRepository(db_conn)

        result = repo.update_phase(UUID(pid), PhaseState.ONBOARDING)

        assert result is not None
        assert result["phase"] == "ONBOARDING"
        assert result["phase_updated_at"] is not None

    def test_update_phase_nonexistent_profile(self, db_conn: sqlite3.Connection) -> None:
        repo = ProfileRepository(db_conn)
        result = repo.update_phase(uuid4(), PhaseState.ACTIVE)
        assert result is None

    def test_update_consent_sets_fields(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid)
        repo = ProfileRepository(db_conn)

        result = repo.update_consent(UUID(pid), "v1.0")

        assert result is not None
        assert result["consent_given_at"] is not None
        assert result["consent_version"] == "v1.0"
        assert result["consent_revoked_at"] is None

    def test_revoke_consent_sets_revoked_at(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid)
        repo = ProfileRepository(db_conn)

        # Grant then revoke
        repo.update_consent(UUID(pid), "v1.0")
        result = repo.revoke_consent(UUID(pid))

        assert result is not None
        assert result["consent_revoked_at"] is not None

    def test_update_consent_clears_revoked_at(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid)
        repo = ProfileRepository(db_conn)

        # Grant, revoke, then re-grant
        repo.update_consent(UUID(pid), "v1.0")
        repo.revoke_consent(UUID(pid))
        result = repo.update_consent(UUID(pid), "v2.0")

        assert result is not None
        assert result["consent_revoked_at"] is None
        assert result["consent_version"] == "v2.0"

    def test_update_last_message(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid)
        repo = ProfileRepository(db_conn)

        result = repo.update_last_message(UUID(pid))

        assert result is not None
        assert result["last_message_at"] is not None

    def test_phase_transitions_round_trip(self, db_conn: sqlite3.Connection) -> None:
        """Walk through several phase changes and verify each persists."""
        uid = _seed_user(db_conn)
        pid = _seed_profile(db_conn, uid, phase="PENDING")
        repo = ProfileRepository(db_conn)

        for phase in [
            PhaseState.ONBOARDING,
            PhaseState.ACTIVE,
            PhaseState.RE_ENGAGING,
            PhaseState.DORMANT,
        ]:
            result = repo.update_phase(UUID(pid), phase)
            assert result is not None
            assert result["phase"] == phase.value

    def test_all_profile_fields_returned(self, db_conn: sqlite3.Connection) -> None:
        """Ensure the dict returned by get_by_user_id has every expected key."""
        uid = _seed_user(db_conn)
        _seed_profile(db_conn, uid)
        repo = ProfileRepository(db_conn)

        result = repo.get_by_user_id(UUID(uid))

        expected_keys = {
            "id",
            "user_id",
            "display_name",
            "timezone",
            "phase",
            "phase_updated_at",
            "consent_given_at",
            "consent_revoked_at",
            "consent_version",
            "onboarding_completed_at",
            "last_message_at",
            "created_at",
            "updated_at",
        }
        assert result is not None
        assert expected_keys.issubset(result.keys())


# ---------------------------------------------------------------------------
# GoalRepository
# ---------------------------------------------------------------------------


class TestGoalRepository:
    """Tests for GoalRepository (10 tests)."""

    def test_create_goal_assigns_uuid(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        goal = repo.create(UUID(uid), "Walk 30 min daily")

        assert goal["id"] is not None
        # Verify it's a valid UUID string
        UUID(goal["id"])

    def test_create_goal_stores_all_fields(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        goal = repo.create(
            UUID(uid),
            title="Run 5K",
            description="Train for a 5K race",
            frequency="3x/week",
            target_per_week=3,
        )

        assert goal["title"] == "Run 5K"
        assert goal["description"] == "Train for a 5K race"
        assert goal["frequency"] == "3x/week"
        assert goal["target_per_week"] == 3
        assert goal["status"] == "active"
        # confirmed default should be False (0 -> bool)
        assert goal["confirmed"] is False

    def test_get_by_user_returns_goals_newest_first(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        repo.create(UUID(uid), "Goal A")
        repo.create(UUID(uid), "Goal B")

        goals = repo.get_by_user(UUID(uid))

        assert len(goals) == 2
        # Newest first (Goal B created after Goal A)
        assert goals[0]["title"] == "Goal B"
        assert goals[1]["title"] == "Goal A"

    def test_get_by_user_empty(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        goals = repo.get_by_user(UUID(uid))
        assert goals == []

    def test_get_active_goals_excludes_non_active(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        repo.create(UUID(uid), "Active Goal")
        g2 = repo.create(UUID(uid), "Paused Goal")

        # Manually pause g2
        db_conn.execute("UPDATE goals SET status = 'paused' WHERE id = ?", (g2["id"],))
        db_conn.commit()

        active = repo.get_active_goals(UUID(uid))

        assert len(active) == 1
        assert active[0]["title"] == "Active Goal"

    def test_get_confirmed_goals(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        g1 = repo.create(UUID(uid), "Goal X")
        repo.create(UUID(uid), "Goal Y")

        repo.confirm_goal(UUID(g1["id"]))

        confirmed = repo.get_confirmed_goals(UUID(uid))

        assert len(confirmed) == 1
        assert confirmed[0]["title"] == "Goal X"
        assert confirmed[0]["confirmed"] is True

    def test_confirm_goal_sets_confirmed_true(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        repo = GoalRepository(db_conn)

        goal = repo.create(UUID(uid), "Some Goal")
        assert goal["confirmed"] is False

        updated = repo.confirm_goal(UUID(goal["id"]))

        assert updated is not None
        assert updated["confirmed"] is True

    def test_confirm_nonexistent_goal_returns_none(self, db_conn: sqlite3.Connection) -> None:
        repo = GoalRepository(db_conn)
        result = repo.confirm_goal(uuid4())
        assert result is None

    def test_goals_attach_milestones(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        goal_repo = GoalRepository(db_conn)
        ms_repo = MilestoneRepository(db_conn)

        goal = goal_repo.create(UUID(uid), "Walk daily")
        ms_repo.create_batch(
            UUID(goal["id"]),
            UUID(uid),
            [
                {"title": "Week 1: 10 min walks", "week_number": 1},
                {"title": "Week 2: 20 min walks", "week_number": 2},
            ],
        )

        goals = goal_repo.get_by_user(UUID(uid))

        assert len(goals) == 1
        assert len(goals[0]["milestones"]) == 2
        assert goals[0]["milestones"][0]["week_number"] == 1
        assert goals[0]["milestones"][1]["week_number"] == 2

    def test_active_goals_attach_milestones(self, db_conn: sqlite3.Connection) -> None:
        uid = _seed_user(db_conn)
        goal_repo = GoalRepository(db_conn)
        ms_repo = MilestoneRepository(db_conn)

        goal = goal_repo.create(UUID(uid), "Stretch routine")
        ms_repo.create_batch(
            UUID(goal["id"]),
            UUID(uid),
            [{"title": "Week 1 milestone", "week_number": 1}],
        )

        active = goal_repo.get_active_goals(UUID(uid))

        assert len(active) == 1
        assert len(active[0]["milestones"]) == 1


# ---------------------------------------------------------------------------
# MilestoneRepository
# ---------------------------------------------------------------------------


class TestMilestoneRepository:
    """Tests for MilestoneRepository (6 tests)."""

    def _make_goal(self, db_conn: sqlite3.Connection) -> tuple[str, str]:
        """Helper: create a user + goal, return (user_id, goal_id)."""
        uid = _seed_user(db_conn)
        goal_repo = GoalRepository(db_conn)
        goal = goal_repo.create(UUID(uid), "Test Goal")
        return uid, goal["id"]

    def test_create_batch_returns_milestones(self, db_conn: sqlite3.Connection) -> None:
        uid, gid = self._make_goal(db_conn)
        repo = MilestoneRepository(db_conn)

        milestones = repo.create_batch(
            UUID(gid),
            UUID(uid),
            [
                {"title": "M1", "description": "First", "week_number": 1},
                {"title": "M2", "week_number": 2},
            ],
        )

        assert len(milestones) == 2
        assert milestones[0]["title"] == "M1"
        assert milestones[0]["description"] == "First"
        assert milestones[1]["title"] == "M2"
        assert milestones[1]["description"] == ""  # default

    def test_create_batch_generates_uuids(self, db_conn: sqlite3.Connection) -> None:
        uid, gid = self._make_goal(db_conn)
        repo = MilestoneRepository(db_conn)

        milestones = repo.create_batch(
            UUID(gid),
            UUID(uid),
            [{"title": "M1", "week_number": 1}],
        )

        UUID(milestones[0]["id"])  # Should not raise

    def test_get_by_goal_ordered_by_week(self, db_conn: sqlite3.Connection) -> None:
        uid, gid = self._make_goal(db_conn)
        repo = MilestoneRepository(db_conn)

        repo.create_batch(
            UUID(gid),
            UUID(uid),
            [
                {"title": "Week 3", "week_number": 3},
                {"title": "Week 1", "week_number": 1},
                {"title": "Week 2", "week_number": 2},
            ],
        )

        fetched = repo.get_by_goal(UUID(gid))

        assert [m["week_number"] for m in fetched] == [1, 2, 3]

    def test_get_by_goal_empty(self, db_conn: sqlite3.Connection) -> None:
        uid, gid = self._make_goal(db_conn)
        repo = MilestoneRepository(db_conn)

        fetched = repo.get_by_goal(UUID(gid))
        assert fetched == []

    def test_mark_completed(self, db_conn: sqlite3.Connection) -> None:
        uid, gid = self._make_goal(db_conn)
        repo = MilestoneRepository(db_conn)

        created = repo.create_batch(
            UUID(gid),
            UUID(uid),
            [{"title": "M1", "week_number": 1}],
        )

        result = repo.mark_completed(UUID(created[0]["id"]))

        assert result is not None
        assert result["completed"] is True
        assert result["completed_at"] is not None

    def test_mark_completed_nonexistent_returns_none(self, db_conn: sqlite3.Connection) -> None:
        repo = MilestoneRepository(db_conn)
        result = repo.mark_completed(uuid4())
        assert result is None

    def test_completed_boolean_round_trip(self, db_conn: sqlite3.Connection) -> None:
        """Verify that the completed column is converted from int to bool."""
        uid, gid = self._make_goal(db_conn)
        repo = MilestoneRepository(db_conn)

        created = repo.create_batch(
            UUID(gid), UUID(uid), [{"title": "M1", "week_number": 1}]
        )

        # Before completion
        fetched = repo.get_by_goal(UUID(gid))
        assert fetched[0]["completed"] is False

        # After completion
        repo.mark_completed(UUID(created[0]["id"]))
        fetched = repo.get_by_goal(UUID(gid))
        assert fetched[0]["completed"] is True


# ---------------------------------------------------------------------------
# ReminderRepository
# ---------------------------------------------------------------------------


class TestReminderRepository:
    """Tests for ReminderRepository (8 tests)."""

    def _uid(self, db_conn: sqlite3.Connection) -> str:
        return _seed_user(db_conn)

    def test_create_reminder(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        due = datetime.now() + timedelta(hours=1)
        reminder = repo.create(UUID(uid), "follow_up", due, "Hey there!", attempt_number=1)

        assert reminder["id"] is not None
        UUID(reminder["id"])
        assert reminder["reminder_type"] == "follow_up"
        assert reminder["message_template"] == "Hey there!"
        assert reminder["attempt_number"] == 1
        assert reminder["status"] == "pending"

    def test_get_due_reminders_returns_past_due_only(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        past_due = datetime.now() - timedelta(hours=1)
        future_due = datetime.now() + timedelta(hours=2)

        repo.create(UUID(uid), "follow_up", past_due)
        repo.create(UUID(uid), "follow_up", future_due)

        due = repo.get_due_reminders()

        assert len(due) == 1
        assert due[0]["user_id"] == uid

    def test_get_due_reminders_excludes_sent(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        past_due = datetime.now() - timedelta(hours=1)
        r = repo.create(UUID(uid), "follow_up", past_due)
        repo.mark_sent(UUID(r["id"]))

        due = repo.get_due_reminders()
        assert len(due) == 0

    def test_get_due_reminders_ordered_by_due_at(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        t1 = datetime.now() - timedelta(hours=3)
        t2 = datetime.now() - timedelta(hours=1)

        repo.create(UUID(uid), "follow_up", t2, "Later")
        repo.create(UUID(uid), "follow_up", t1, "Earlier")

        due = repo.get_due_reminders()

        assert len(due) == 2
        assert due[0]["message_template"] == "Earlier"
        assert due[1]["message_template"] == "Later"

    def test_mark_sent(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        r = repo.create(UUID(uid), "follow_up", datetime.now() - timedelta(hours=1))
        result = repo.mark_sent(UUID(r["id"]))

        assert result is not None
        assert result["status"] == "sent"
        assert result["sent_at"] is not None

    def test_mark_failed(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        r = repo.create(UUID(uid), "follow_up", datetime.now())
        result = repo.mark_failed(UUID(r["id"]))

        assert result is not None
        assert result["status"] == "failed"

    def test_get_attempt_count(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        # Create 3 follow_up reminders and send 2 of them
        for i in range(3):
            r = repo.create(UUID(uid), "follow_up", datetime.now() - timedelta(hours=1))
            if i < 2:
                repo.mark_sent(UUID(r["id"]))

        count = repo.get_attempt_count(UUID(uid))
        assert count == 2

    def test_get_attempt_count_ignores_non_follow_up(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ReminderRepository(db_conn)

        r = repo.create(UUID(uid), "nudge", datetime.now() - timedelta(hours=1))
        repo.mark_sent(UUID(r["id"]))

        count = repo.get_attempt_count(UUID(uid))
        assert count == 0


# ---------------------------------------------------------------------------
# ConversationRepository
# ---------------------------------------------------------------------------


class TestConversationRepository:
    """Tests for ConversationRepository (7 tests)."""

    def _uid(self, db_conn: sqlite3.Connection) -> str:
        return _seed_user(db_conn)

    def test_add_turn_basic(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        turn = repo.add_turn(UUID(uid), "user", "Hello!", "ONBOARDING", 1)

        assert turn["id"] is not None
        UUID(turn["id"])
        assert turn["role"] == "user"
        assert turn["content"] == "Hello!"
        assert turn["phase"] == "ONBOARDING"
        assert turn["turn_number"] == 1

    def test_add_turn_with_tool_calls_json(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        tc = {"name": "set_goal", "args": {"title": "Walk"}}
        tr = {"result": "Goal set"}

        turn = repo.add_turn(
            UUID(uid), "assistant", "Setting goal...", "ACTIVE", 2,
            tool_calls=tc, tool_results=tr,
        )

        assert turn["tool_calls"] == tc
        assert turn["tool_results"] == tr

    def test_add_turn_null_tool_calls(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        turn = repo.add_turn(UUID(uid), "user", "Hi", "PENDING", 1)

        assert turn["tool_calls"] is None
        assert turn["tool_results"] is None

    def test_get_recent_turns_ascending_order(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        repo.add_turn(UUID(uid), "user", "First", "ONBOARDING", 1)
        repo.add_turn(UUID(uid), "assistant", "Second", "ONBOARDING", 2)
        repo.add_turn(UUID(uid), "user", "Third", "ONBOARDING", 3)

        turns = repo.get_recent_turns(UUID(uid), limit=10)

        assert len(turns) == 3
        # Should be in ascending turn_number order after the reverse()
        assert turns[0]["content"] == "First"
        assert turns[1]["content"] == "Second"
        assert turns[2]["content"] == "Third"

    def test_get_recent_turns_respects_limit(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        for i in range(5):
            repo.add_turn(UUID(uid), "user", f"Turn {i}", "ACTIVE", i + 1)

        turns = repo.get_recent_turns(UUID(uid), limit=2)

        assert len(turns) == 2
        # The most recent 2 turns should be turn 4 and 5 (ascending after reverse)
        assert turns[0]["content"] == "Turn 3"
        assert turns[1]["content"] == "Turn 4"

    def test_get_turn_count(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        assert repo.get_turn_count(UUID(uid)) == 0

        repo.add_turn(UUID(uid), "user", "A", "PENDING", 1)
        repo.add_turn(UUID(uid), "assistant", "B", "PENDING", 2)

        assert repo.get_turn_count(UUID(uid)) == 2

    def test_get_recent_turns_empty(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        turns = repo.get_recent_turns(UUID(uid))
        assert turns == []

    def test_token_counts_stored(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = ConversationRepository(db_conn)

        turn = repo.add_turn(
            UUID(uid), "assistant", "Response", "ACTIVE", 1,
            token_count_input=150, token_count_output=80,
        )

        assert turn["token_count_input"] == 150
        assert turn["token_count_output"] == 80


# ---------------------------------------------------------------------------
# SafetyAuditRepository
# ---------------------------------------------------------------------------


class TestSafetyAuditRepository:
    """Tests for SafetyAuditRepository (6 tests)."""

    def _uid(self, db_conn: sqlite3.Connection) -> str:
        return _seed_user(db_conn)

    def test_log_entry_basic(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SafetyAuditRepository(db_conn)

        entry = repo.log_entry(
            UUID(uid),
            input_text="I feel good about my exercises",
            classification=SafetyClassificationType.SAFE,
            confidence=0.95,
            action_taken=SafetyAction.PASSED,
        )

        assert entry["id"] is not None
        UUID(entry["id"])
        assert entry["classification"] == "safe"
        assert entry["confidence"] == 0.95
        assert entry["action_taken"] == "passed"
        assert entry["tier"] == "llm"  # default

    def test_log_entry_with_categories_and_flagged_phrases(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SafetyAuditRepository(db_conn)

        cats = ["medication", "dosage"]
        phrases = ["take 200mg", "prescription"]

        entry = repo.log_entry(
            UUID(uid),
            input_text="Should I take 200mg of ibuprofen?",
            classification=SafetyClassificationType.CLINICAL,
            confidence=0.85,
            action_taken=SafetyAction.REWRITTEN,
            categories=cats,
            flagged_phrases=phrases,
        )

        # JSON round-trip
        assert entry["categories"] == cats
        assert entry["flagged_phrases"] == phrases

    def test_log_entry_empty_categories_default(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SafetyAuditRepository(db_conn)

        entry = repo.log_entry(
            UUID(uid),
            input_text="Hi",
            classification=SafetyClassificationType.SAFE,
            confidence=0.99,
            action_taken=SafetyAction.PASSED,
        )

        # Default: empty lists
        assert entry["categories"] == []
        assert entry["flagged_phrases"] == []

    def test_log_entry_with_conversation_turn_id(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        conv_repo = ConversationRepository(db_conn)
        turn = conv_repo.add_turn(UUID(uid), "user", "Test", "ACTIVE", 1)

        repo = SafetyAuditRepository(db_conn)
        entry = repo.log_entry(
            UUID(uid),
            input_text="Test",
            classification=SafetyClassificationType.SAFE,
            confidence=0.9,
            action_taken=SafetyAction.PASSED,
            conversation_turn_id=UUID(turn["id"]),
        )

        assert entry["conversation_turn_id"] == turn["id"]

    def test_get_recent_entries_newest_first(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SafetyAuditRepository(db_conn)

        repo.log_entry(
            UUID(uid), "First", SafetyClassificationType.SAFE,
            0.9, SafetyAction.PASSED, reasoning="first",
        )
        repo.log_entry(
            UUID(uid), "Second", SafetyClassificationType.CLINICAL,
            0.7, SafetyAction.REWRITTEN, reasoning="second",
        )

        entries = repo.get_recent_entries(UUID(uid))

        assert len(entries) == 2
        # Newest first (ORDER BY created_at DESC)
        assert entries[0]["reasoning"] == "second"
        assert entries[1]["reasoning"] == "first"

    def test_get_recent_entries_respects_limit(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SafetyAuditRepository(db_conn)

        for i in range(5):
            repo.log_entry(
                UUID(uid), f"Input {i}", SafetyClassificationType.SAFE,
                0.9, SafetyAction.PASSED,
            )

        entries = repo.get_recent_entries(UUID(uid), limit=2)
        assert len(entries) == 2


# ---------------------------------------------------------------------------
# SummaryRepository
# ---------------------------------------------------------------------------


class TestSummaryRepository:
    """Tests for SummaryRepository (5 tests)."""

    def _uid(self, db_conn: sqlite3.Connection) -> str:
        return _seed_user(db_conn)

    def test_create_summary(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SummaryRepository(db_conn)

        summary = repo.create(UUID(uid), "User discussed walking goals.", 1, 6)

        assert summary["id"] is not None
        UUID(summary["id"])
        assert summary["summary_text"] == "User discussed walking goals."
        assert summary["turns_covered_from"] == 1
        assert summary["turns_covered_to"] == 6

    def test_get_latest_returns_most_recent(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SummaryRepository(db_conn)

        repo.create(UUID(uid), "Old summary.", 1, 6)
        repo.create(UUID(uid), "New summary.", 7, 12)

        latest = repo.get_latest(UUID(uid))

        assert latest is not None
        assert latest["summary_text"] == "New summary."
        assert latest["turns_covered_from"] == 7
        assert latest["turns_covered_to"] == 12

    def test_get_latest_returns_none_when_empty(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SummaryRepository(db_conn)

        result = repo.get_latest(UUID(uid))
        assert result is None

    def test_multiple_summaries_stored(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SummaryRepository(db_conn)

        repo.create(UUID(uid), "S1", 1, 6)
        repo.create(UUID(uid), "S2", 7, 12)
        repo.create(UUID(uid), "S3", 13, 18)

        # All three exist in the table
        rows = db_conn.execute(
            "SELECT COUNT(*) FROM conversation_summaries WHERE user_id = ?",
            (uid,),
        ).fetchone()
        assert rows[0] == 3

    def test_summary_fields_round_trip(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = SummaryRepository(db_conn)

        summary = repo.create(UUID(uid), "Detailed summary text here.", 5, 10)

        # Re-fetch from DB
        latest = repo.get_latest(UUID(uid))
        assert latest is not None
        assert latest["id"] == summary["id"]
        assert latest["user_id"] == uid
        assert latest["created_at"] is not None


# ---------------------------------------------------------------------------
# AlertRepository
# ---------------------------------------------------------------------------


class TestAlertRepository:
    """Tests for AlertRepository (7 tests)."""

    def _uid(self, db_conn: sqlite3.Connection) -> str:
        return _seed_user(db_conn)

    def test_create_alert_default_urgency(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        alert = repo.create(UUID(uid), "safety_concern", message="Patient flagged")

        assert alert["id"] is not None
        UUID(alert["id"])
        assert alert["alert_type"] == "safety_concern"
        assert alert["urgency"] == "routine"
        assert alert["status"] == "pending"
        assert alert["message"] == "Patient flagged"

    def test_create_alert_urgent(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        alert = repo.create(
            UUID(uid), "crisis", urgency=AlertUrgency.URGENT, message="Crisis detected"
        )

        assert alert["urgency"] == "urgent"

    def test_create_alert_with_safety_audit_id(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        safety_repo = SafetyAuditRepository(db_conn)
        audit = safety_repo.log_entry(
            UUID(uid), "Bad input", SafetyClassificationType.CRISIS,
            0.99, SafetyAction.ESCALATED,
        )

        alert_repo = AlertRepository(db_conn)
        alert = alert_repo.create(
            UUID(uid), "crisis", urgency=AlertUrgency.URGENT,
            message="Crisis!", safety_audit_id=UUID(audit["id"]),
        )

        assert alert["safety_audit_id"] == audit["id"]

    def test_get_unacknowledged_returns_pending_only(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        a1 = repo.create(UUID(uid), "issue1", message="First")
        repo.create(UUID(uid), "issue2", message="Second")

        repo.acknowledge(UUID(a1["id"]), notes="Reviewed")

        unacked = repo.get_unacknowledged()

        assert len(unacked) == 1
        assert unacked[0]["message"] == "Second"

    def test_acknowledge_alert(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        alert = repo.create(UUID(uid), "concern", message="Check this")
        result = repo.acknowledge(UUID(alert["id"]), notes="Handled by Dr. Smith")

        assert result is not None
        assert result["status"] == "acknowledged"
        assert result["acknowledged_at"] is not None
        assert result["notes"] == "Handled by Dr. Smith"

    def test_acknowledge_nonexistent_returns_none(self, db_conn: sqlite3.Connection) -> None:
        repo = AlertRepository(db_conn)
        result = repo.acknowledge(uuid4())
        assert result is None

    def test_get_unacknowledged_newest_first(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        repo.create(UUID(uid), "a", message="Older")
        repo.create(UUID(uid), "b", message="Newer")

        unacked = repo.get_unacknowledged()

        assert len(unacked) == 2
        # ORDER BY created_at DESC
        assert unacked[0]["message"] == "Newer"
        assert unacked[1]["message"] == "Older"

    def test_get_unacknowledged_empty(self, db_conn: sqlite3.Connection) -> None:
        repo = AlertRepository(db_conn)
        unacked = repo.get_unacknowledged()
        assert unacked == []

    def test_count_by_user(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        repo.create(UUID(uid), "issue1", message="First")
        repo.create(UUID(uid), "issue2", message="Second")

        assert repo.count_by_user(UUID(uid)) == 2

    def test_count_by_user_excludes_acknowledged(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)

        a1 = repo.create(UUID(uid), "issue1", message="First")
        repo.create(UUID(uid), "issue2", message="Second")
        repo.acknowledge(UUID(a1["id"]))

        assert repo.count_by_user(UUID(uid)) == 1

    def test_count_by_user_empty(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        repo = AlertRepository(db_conn)
        assert repo.count_by_user(UUID(uid)) == 0

    def test_get_unacknowledged_with_patient_includes_name(self, db_conn: sqlite3.Connection) -> None:
        uid = self._uid(db_conn)
        # Need a profile for the JOIN
        _seed_profile(db_conn, uid)
        repo = AlertRepository(db_conn)

        repo.create(UUID(uid), "concern", message="Check patient")

        results = repo.get_unacknowledged_with_patient()
        assert len(results) == 1
        assert results[0]["patient_name"] is not None


class TestProfileRepositoryGetAll:
    """Tests for ProfileRepository.get_all()."""

    def test_get_all_returns_all_profiles(self, db_conn: sqlite3.Connection) -> None:
        from src.db.repositories import ProfileRepository

        # Seed some profiles
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "a@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u2", "b@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
            ("p1", "u1", "Alice"),
        )
        db_conn.execute(
            "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
            ("p2", "u2", "Bob"),
        )
        db_conn.commit()

        repo = ProfileRepository(db_conn)
        profiles = repo.get_all()

        assert len(profiles) == 2
        # Sorted by display_name
        assert profiles[0]["display_name"] == "Alice"
        assert profiles[1]["display_name"] == "Bob"

    def test_get_all_empty(self, db_conn: sqlite3.Connection) -> None:
        from src.db.repositories import ProfileRepository

        repo = ProfileRepository(db_conn)
        profiles = repo.get_all()
        assert profiles == []
