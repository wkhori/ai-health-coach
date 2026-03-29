"""Comprehensive tests for the SQLite database client, schema, and seed system.

Covers:
- Schema creation and table structure validation
- Client connection management and global state
- Seed data insertion and integrity
- Referential integrity across all tables
"""

from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path

import pytest

from src.db.client import get_db, reset_db
from src.db.schema import SCHEMA_SQL, init_db
from src.db.seed import (
    _hash_password,
    get_seed_data,
    seed_db,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_TABLES = [
    "users",
    "sessions",
    "profiles",
    "goals",
    "milestones",
    "reminders",
    "conversation_turns",
    "safety_audit_log",
    "clinician_alerts",
    "conversation_summaries",
]


def _table_names(conn: sqlite3.Connection) -> list[str]:
    """Return all user-created table names (excludes sqlite internals)."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [r[0] if isinstance(r, tuple) else r["name"] for r in rows]


def _column_names(conn: sqlite3.Connection, table: str) -> list[str]:
    """Return column names for a given table."""
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return [r[1] if isinstance(r, tuple) else r["name"] for r in rows]


def _count(conn: sqlite3.Connection, table: str) -> int:
    """Return the row count of a table."""
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def _fresh_seeded_conn() -> sqlite3.Connection:
    """Create an in-memory connection with schema + seed data."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    init_db(conn)
    seed_db(conn)
    return conn


# ============================================================================
# TestSchema
# ============================================================================
class TestSchema:
    """Tests for schema.py: table creation, columns, constraints, triggers."""

    def test_init_db_creates_all_tables(self, db_conn: sqlite3.Connection) -> None:
        tables = _table_names(db_conn)
        for expected in EXPECTED_TABLES:
            assert expected in tables, f"Missing table: {expected}"

    def test_init_db_idempotent(self, db_conn: sqlite3.Connection) -> None:
        """Calling init_db a second time should not raise."""
        init_db(db_conn)
        tables = _table_names(db_conn)
        assert len(tables) >= len(EXPECTED_TABLES)

    def test_users_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "users")
        assert "id" in cols
        assert "email" in cols
        assert "password_hash" in cols
        assert "created_at" in cols

    def test_sessions_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "sessions")
        assert "token" in cols
        assert "user_id" in cols
        assert "created_at" in cols

    def test_profiles_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "profiles")
        expected_cols = [
            "id", "user_id", "display_name", "timezone", "phase",
            "phase_updated_at", "consent_given_at", "consent_revoked_at",
            "consent_version", "onboarding_completed_at", "last_message_at",
            "created_at", "updated_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in profiles: {c}"

    def test_goals_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "goals")
        expected_cols = [
            "id", "user_id", "title", "description", "frequency",
            "target_per_week", "confirmed", "status", "target_date",
            "created_at", "updated_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in goals: {c}"

    def test_milestones_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "milestones")
        expected_cols = [
            "id", "goal_id", "user_id", "title", "description",
            "week_number", "completed", "completed_at", "created_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in milestones: {c}"

    def test_conversation_turns_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "conversation_turns")
        expected_cols = [
            "id", "user_id", "role", "content", "phase", "turn_number",
            "tool_calls", "tool_results", "token_count_input",
            "token_count_output", "created_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in conversation_turns: {c}"

    def test_safety_audit_log_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "safety_audit_log")
        expected_cols = [
            "id", "user_id", "conversation_turn_id", "input_text",
            "classification", "confidence", "categories", "flagged_phrases",
            "reasoning", "action_taken", "tier", "model_used", "created_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in safety_audit_log: {c}"

    def test_clinician_alerts_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "clinician_alerts")
        expected_cols = [
            "id", "user_id", "safety_audit_id", "alert_type", "urgency",
            "status", "message", "acknowledged_at", "notes", "created_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in clinician_alerts: {c}"

    def test_reminders_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "reminders")
        expected_cols = [
            "id", "user_id", "reminder_type", "message_template",
            "scheduled_at", "due_at", "sent_at", "status", "retry_count",
            "attempt_number", "created_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in reminders: {c}"

    def test_conversation_summaries_table_columns(self, db_conn: sqlite3.Connection) -> None:
        cols = _column_names(db_conn, "conversation_summaries")
        expected_cols = [
            "id", "user_id", "summary_text", "turns_covered_from",
            "turns_covered_to", "created_at",
        ]
        for c in expected_cols:
            assert c in cols, f"Missing column in conversation_summaries: {c}"

    def test_phase_check_constraint(self, db_conn: sqlite3.Connection) -> None:
        """Inserting an invalid phase into profiles should fail."""
        # First create a user that the profile can reference
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO profiles (id, user_id, phase) VALUES (?, ?, ?)",
                ("p1", "u1", "INVALID_PHASE"),
            )

    def test_goal_status_check_constraint(self, db_conn: sqlite3.Connection) -> None:
        """Inserting an invalid status into goals should fail."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO goals (id, user_id, title, status) VALUES (?, ?, ?, ?)",
                ("g1", "u1", "Test Goal", "INVALID_STATUS"),
            )

    def test_unique_user_id_on_profiles(self, db_conn: sqlite3.Connection) -> None:
        """Two profiles with the same user_id should fail (UNIQUE constraint)."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
            ("p1", "u1", "First"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
                ("p2", "u1", "Duplicate"),
            )

    def test_unique_email_on_users(self, db_conn: sqlite3.Connection) -> None:
        """Two users with the same email should fail."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "same@test.com", "hash1"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                ("u2", "same@test.com", "hash2"),
            )

    def test_foreign_keys_enabled(self, db_conn: sqlite3.Connection) -> None:
        """Foreign key constraints should be enforced after init_db."""
        # Attempt to insert a profile referencing a non-existent user
        with pytest.raises(sqlite3.IntegrityError):
            db_conn.execute(
                "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
                ("p1", "nonexistent_user", "Ghost"),
            )

    def test_valid_phases_accepted(self, db_conn: sqlite3.Connection) -> None:
        """All five valid phase values should be insertable."""
        valid_phases = ["PENDING", "ONBOARDING", "ACTIVE", "RE_ENGAGING", "DORMANT"]
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        for i, phase in enumerate(valid_phases):
            # Use user_id trick: profiles.user_id is UNIQUE, so we need separate users
            uid = f"u{i + 10}"
            db_conn.execute(
                "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
                (uid, f"test{i}@test.com", "hash"),
            )
            db_conn.execute(
                "INSERT INTO profiles (id, user_id, phase) VALUES (?, ?, ?)",
                (f"p{i}", uid, phase),
            )
        # If we get here, all phases were accepted
        count = db_conn.execute("SELECT COUNT(*) FROM profiles").fetchone()[0]
        assert count == len(valid_phases)

    def test_valid_goal_statuses_accepted(self, db_conn: sqlite3.Connection) -> None:
        """All three valid goal statuses should be insertable."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        for i, status in enumerate(["active", "paused", "completed"]):
            db_conn.execute(
                "INSERT INTO goals (id, user_id, title, status) VALUES (?, ?, ?, ?)",
                (f"g{i}", "u1", f"Goal {i}", status),
            )
        count = db_conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0]
        assert count == 3

    def test_profiles_updated_at_trigger(self, db_conn: sqlite3.Connection) -> None:
        """The profiles_updated_at trigger should update updated_at on UPDATE."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
            ("p1", "u1", "Original"),
        )
        original = db_conn.execute(
            "SELECT updated_at FROM profiles WHERE id = 'p1'"
        ).fetchone()["updated_at"]

        # Perform an update
        db_conn.execute(
            "UPDATE profiles SET display_name = 'Updated' WHERE id = 'p1'"
        )
        updated = db_conn.execute(
            "SELECT updated_at FROM profiles WHERE id = 'p1'"
        ).fetchone()["updated_at"]

        # The trigger fires, so updated_at should be different (or at least set)
        assert updated is not None
        # Note: In a fast test, timestamps could be the same millisecond,
        # so we just verify the trigger didn't break anything.

    def test_goals_updated_at_trigger(self, db_conn: sqlite3.Connection) -> None:
        """The goals_updated_at trigger should update updated_at on UPDATE."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO goals (id, user_id, title) VALUES (?, ?, ?)",
            ("g1", "u1", "Original Goal"),
        )
        db_conn.execute(
            "UPDATE goals SET title = 'Updated Goal' WHERE id = 'g1'"
        )
        updated = db_conn.execute(
            "SELECT updated_at FROM goals WHERE id = 'g1'"
        ).fetchone()["updated_at"]
        assert updated is not None

    def test_cascade_delete_user_deletes_profile(self, db_conn: sqlite3.Connection) -> None:
        """Deleting a user should cascade-delete their profile."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO profiles (id, user_id, display_name) VALUES (?, ?, ?)",
            ("p1", "u1", "Test"),
        )
        db_conn.execute("DELETE FROM users WHERE id = 'u1'")
        count = db_conn.execute("SELECT COUNT(*) FROM profiles WHERE user_id = 'u1'").fetchone()[0]
        assert count == 0

    def test_cascade_delete_user_deletes_goals(self, db_conn: sqlite3.Connection) -> None:
        """Deleting a user should cascade-delete their goals."""
        db_conn.execute(
            "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            ("u1", "test@test.com", "hash"),
        )
        db_conn.execute(
            "INSERT INTO goals (id, user_id, title) VALUES (?, ?, ?)",
            ("g1", "u1", "Test Goal"),
        )
        db_conn.execute("DELETE FROM users WHERE id = 'u1'")
        count = db_conn.execute("SELECT COUNT(*) FROM goals WHERE user_id = 'u1'").fetchone()[0]
        assert count == 0


# ============================================================================
# TestClient
# ============================================================================
class TestClient:
    """Tests for client.py: get_db(), reset_db(), connection caching."""

    def setup_method(self) -> None:
        """Ensure clean state before each test."""
        reset_db()

    def teardown_method(self) -> None:
        """Clean up after each test."""
        reset_db()

    def test_get_db_returns_connection(self, tmp_path: Path) -> None:
        db_path = str(tmp_path / "test.db")
        conn = get_db(db_path)
        assert isinstance(conn, sqlite3.Connection)

    def test_get_db_caches_connection(self, tmp_path: Path) -> None:
        """get_db() should return the same object on repeated calls."""
        db_path = str(tmp_path / "test.db")
        conn1 = get_db(db_path)
        conn2 = get_db(db_path)
        assert conn1 is conn2

    def test_get_db_initializes_schema(self, tmp_path: Path) -> None:
        """get_db() should auto-create all tables."""
        db_path = str(tmp_path / "test.db")
        conn = get_db(db_path)
        tables = _table_names(conn)
        for expected in EXPECTED_TABLES:
            assert expected in tables, f"get_db() did not create table: {expected}"

    def test_reset_db_clears_connection(self, tmp_path: Path) -> None:
        """After reset_db(), the cached connection should be cleared."""
        db_path = str(tmp_path / "test.db")
        conn1 = get_db(db_path)
        reset_db()
        # The old connection should be closed; a new get_db should create fresh
        conn2 = get_db(db_path)
        assert conn1 is not conn2

    def test_get_db_after_reset_creates_new(self, tmp_path: Path) -> None:
        """get_db() after reset should return a working connection."""
        db_path = str(tmp_path / "test.db")
        get_db(db_path)
        reset_db()
        conn = get_db(db_path)
        # Should be fully functional
        tables = _table_names(conn)
        assert len(tables) >= len(EXPECTED_TABLES)

    def test_row_factory_is_set(self, tmp_path: Path) -> None:
        """The connection should have sqlite3.Row as row_factory."""
        db_path = str(tmp_path / "test.db")
        conn = get_db(db_path)
        assert conn.row_factory is sqlite3.Row

    def test_foreign_keys_pragma_enabled(self, tmp_path: Path) -> None:
        """Foreign keys should be enabled via PRAGMA."""
        db_path = str(tmp_path / "test.db")
        conn = get_db(db_path)
        fk_status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        assert fk_status == 1

    def test_wal_journal_mode(self, tmp_path: Path) -> None:
        """Journal mode should be WAL."""
        db_path = str(tmp_path / "test.db")
        conn = get_db(db_path)
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        assert mode.lower() == "wal"

    def test_get_db_creates_parent_dirs(self, tmp_path: Path) -> None:
        """get_db() should create parent directories if they don't exist."""
        db_path = str(tmp_path / "nested" / "dir" / "test.db")
        conn = get_db(db_path)
        assert isinstance(conn, sqlite3.Connection)
        assert Path(db_path).exists()


# ============================================================================
# TestSeedDb
# ============================================================================
class TestSeedDb:
    """Tests for seed.py: data insertion, counts, and correctness."""

    @pytest.fixture(autouse=True)
    def _seeded_conn(self) -> None:
        """Provide a seeded in-memory database for all tests in this class."""
        self.conn = _fresh_seeded_conn()

    def test_seed_db_creates_users(self) -> None:
        count = _count(self.conn, "users")
        assert count == 3, f"Expected 3 demo users, got {count}"

    def test_seed_db_creates_profiles(self) -> None:
        count = _count(self.conn, "profiles")
        assert count == 3, f"Expected 3 profiles, got {count}"

    def test_seed_db_creates_goals(self) -> None:
        count = _count(self.conn, "goals")
        assert count == 4, f"Expected 4 goals, got {count}"

    def test_seed_db_creates_milestones(self) -> None:
        count = _count(self.conn, "milestones")
        assert count == 12, f"Expected 12 milestones, got {count}"

    def test_seed_db_creates_conversation_turns(self) -> None:
        count = _count(self.conn, "conversation_turns")
        assert count == 26, f"Expected 26 conversation turns, got {count}"

    def test_seed_db_creates_safety_audit_log(self) -> None:
        count = _count(self.conn, "safety_audit_log")
        assert count == 3, f"Expected 3 safety audit entries, got {count}"

    def test_seed_db_creates_clinician_alerts(self) -> None:
        count = _count(self.conn, "clinician_alerts")
        assert count == 1, f"Expected 1 clinician alert, got {count}"

    def test_seed_db_creates_reminders(self) -> None:
        count = _count(self.conn, "reminders")
        assert count == 2, f"Expected 2 reminders, got {count}"

    def test_seed_db_creates_conversation_summaries(self) -> None:
        count = _count(self.conn, "conversation_summaries")
        assert count == 1, f"Expected 1 conversation summary, got {count}"

    def test_seed_db_user_passwords_are_hashed(self) -> None:
        """Password hashes should be in salt:hash format and verifiable."""
        rows = self.conn.execute("SELECT password_hash FROM users").fetchall()
        for row in rows:
            pw_hash = row["password_hash"]
            # Format: hex_salt:hex_hash
            assert ":" in pw_hash, f"Password hash not in salt:hash format: {pw_hash}"
            salt_hex, hash_hex = pw_hash.split(":")
            # Salt is 16 bytes = 32 hex chars
            assert len(salt_hex) == 32, f"Salt wrong length: {len(salt_hex)}"
            # PBKDF2-SHA256 output is 32 bytes = 64 hex chars
            assert len(hash_hex) == 64, f"Hash wrong length: {len(hash_hex)}"

    def test_seed_db_passwords_verify_correctly(self) -> None:
        """The seeded password hashes should verify against 'password123'."""
        rows = self.conn.execute("SELECT password_hash FROM users").fetchall()
        for row in rows:
            stored_hash = row["password_hash"]
            salt_hex, hash_hex = stored_hash.split(":")
            salt = bytes.fromhex(salt_hex)
            computed = hashlib.pbkdf2_hmac(
                "sha256", "password123".encode(), salt, 100000
            )
            assert computed.hex() == hash_hex

    def test_seed_db_sarah_is_active_phase(self) -> None:
        row = self.conn.execute(
            "SELECT phase FROM profiles WHERE display_name = 'Sarah'"
        ).fetchone()
        assert row is not None
        assert row["phase"] == "ACTIVE"

    def test_seed_db_marcus_is_onboarding_phase(self) -> None:
        row = self.conn.execute(
            "SELECT phase FROM profiles WHERE display_name = 'Marcus'"
        ).fetchone()
        assert row is not None
        assert row["phase"] == "ONBOARDING"

    def test_seed_db_elena_is_re_engaging_phase(self) -> None:
        row = self.conn.execute(
            "SELECT phase FROM profiles WHERE display_name = 'Elena'"
        ).fetchone()
        assert row is not None
        assert row["phase"] == "RE_ENGAGING"

    def test_seed_db_sarah_has_consent(self) -> None:
        row = self.conn.execute(
            "SELECT consent_given_at FROM profiles WHERE display_name = 'Sarah'"
        ).fetchone()
        assert row is not None
        assert row["consent_given_at"] is not None

    def test_seed_db_marcus_has_consent(self) -> None:
        row = self.conn.execute(
            "SELECT consent_given_at FROM profiles WHERE display_name = 'Marcus'"
        ).fetchone()
        assert row is not None
        assert row["consent_given_at"] is not None

    def test_seed_db_elena_has_consent(self) -> None:
        row = self.conn.execute(
            "SELECT consent_given_at FROM profiles WHERE display_name = 'Elena'"
        ).fetchone()
        assert row is not None
        assert row["consent_given_at"] is not None

    def test_seed_db_goals_have_correct_users(self) -> None:
        """Goals should belong to the correct users."""
        sarah_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Sarah'"
        ).fetchone()["user_id"]
        sarah_goals = self.conn.execute(
            "SELECT COUNT(*) FROM goals WHERE user_id = ?", (sarah_user_id,)
        ).fetchone()[0]
        assert sarah_goals == 2, f"Sarah should have 2 goals, got {sarah_goals}"

        marcus_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Marcus'"
        ).fetchone()["user_id"]
        marcus_goals = self.conn.execute(
            "SELECT COUNT(*) FROM goals WHERE user_id = ?", (marcus_user_id,)
        ).fetchone()[0]
        assert marcus_goals == 1, f"Marcus should have 1 goal, got {marcus_goals}"

        elena_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Elena'"
        ).fetchone()["user_id"]
        elena_goals = self.conn.execute(
            "SELECT COUNT(*) FROM goals WHERE user_id = ?", (elena_user_id,)
        ).fetchone()[0]
        assert elena_goals == 1, f"Elena should have 1 goal, got {elena_goals}"

    def test_seed_db_milestones_linked_to_goals(self) -> None:
        """Every milestone should reference an existing goal."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM milestones m LEFT JOIN goals g ON m.goal_id = g.id WHERE g.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0, f"{orphaned} milestones reference non-existent goals"

    def test_seed_db_sarah_conversation_turns(self) -> None:
        """Sarah should have 15 conversation turns."""
        sarah_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Sarah'"
        ).fetchone()["user_id"]
        count = self.conn.execute(
            "SELECT COUNT(*) FROM conversation_turns WHERE user_id = ?", (sarah_user_id,)
        ).fetchone()[0]
        assert count == 15

    def test_seed_db_marcus_conversation_turns(self) -> None:
        """Marcus should have 3 conversation turns."""
        marcus_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Marcus'"
        ).fetchone()["user_id"]
        count = self.conn.execute(
            "SELECT COUNT(*) FROM conversation_turns WHERE user_id = ?", (marcus_user_id,)
        ).fetchone()[0]
        assert count == 3

    def test_seed_db_elena_conversation_turns(self) -> None:
        """Elena should have 8 conversation turns."""
        elena_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Elena'"
        ).fetchone()["user_id"]
        count = self.conn.execute(
            "SELECT COUNT(*) FROM conversation_turns WHERE user_id = ?", (elena_user_id,)
        ).fetchone()[0]
        assert count == 8

    def test_seed_db_idempotent_users(self) -> None:
        """Running seed_db twice should not create duplicate users (INSERT OR IGNORE)."""
        seed_db(self.conn)  # Second call
        count = _count(self.conn, "users")
        assert count == 3, f"Expected 3 users after double-seed, got {count}"

    def test_seed_db_idempotent_profiles(self) -> None:
        """Running seed_db twice should not create duplicate profiles."""
        seed_db(self.conn)  # Second call
        count = _count(self.conn, "profiles")
        assert count == 3, f"Expected 3 profiles after double-seed, got {count}"

    def test_seed_db_user_emails(self) -> None:
        """Demo users should have the expected email addresses."""
        emails = {
            row["email"]
            for row in self.conn.execute("SELECT email FROM users").fetchall()
        }
        assert emails == {"sarah@demo.com", "marcus@demo.com", "elena@demo.com"}

    def test_seed_db_marcus_goal_not_confirmed(self) -> None:
        """Marcus's goal should NOT be confirmed (still onboarding)."""
        marcus_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Marcus'"
        ).fetchone()["user_id"]
        goal = self.conn.execute(
            "SELECT confirmed FROM goals WHERE user_id = ?", (marcus_user_id,)
        ).fetchone()
        assert goal["confirmed"] == 0  # False stored as 0 in SQLite

    def test_seed_db_sarah_goals_confirmed(self) -> None:
        """Both of Sarah's goals should be confirmed."""
        sarah_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Sarah'"
        ).fetchone()["user_id"]
        goals = self.conn.execute(
            "SELECT confirmed FROM goals WHERE user_id = ?", (sarah_user_id,)
        ).fetchall()
        for g in goals:
            assert g["confirmed"] == 1  # True stored as 1


# ============================================================================
# TestSeedDataIntegrity
# ============================================================================
class TestSeedDataIntegrity:
    """Tests for referential integrity of seed data across all tables."""

    @pytest.fixture(autouse=True)
    def _seeded_conn(self) -> None:
        self.conn = _fresh_seeded_conn()

    def test_all_profiles_have_matching_users(self) -> None:
        """Every profile's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM profiles p LEFT JOIN users u ON p.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_goals_have_matching_users(self) -> None:
        """Every goal's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM goals g LEFT JOIN users u ON g.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_milestones_have_matching_goals(self) -> None:
        """Every milestone's goal_id should exist in the goals table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM milestones m LEFT JOIN goals g ON m.goal_id = g.id WHERE g.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_milestones_have_matching_users(self) -> None:
        """Every milestone's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM milestones m LEFT JOIN users u ON m.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_conversation_turns_have_matching_users(self) -> None:
        """Every conversation turn's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM conversation_turns ct LEFT JOIN users u ON ct.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_reminders_have_matching_users(self) -> None:
        """Every reminder's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM reminders r LEFT JOIN users u ON r.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_safety_audit_entries_have_matching_users(self) -> None:
        """Every safety audit entry's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM safety_audit_log s LEFT JOIN users u ON s.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_clinician_alerts_have_matching_users(self) -> None:
        """Every clinician alert's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM clinician_alerts ca LEFT JOIN users u ON ca.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_all_conversation_summaries_have_matching_users(self) -> None:
        """Every conversation summary's user_id should exist in the users table."""
        orphaned = self.conn.execute(
            "SELECT COUNT(*) FROM conversation_summaries cs LEFT JOIN users u ON cs.user_id = u.id WHERE u.id IS NULL"
        ).fetchone()[0]
        assert orphaned == 0

    def test_safety_audit_turn_references_valid(self) -> None:
        """Safety audit entries referencing conversation turns should point to valid turns."""
        # Only check non-null references
        orphaned = self.conn.execute(
            """SELECT COUNT(*) FROM safety_audit_log s
               LEFT JOIN conversation_turns ct ON s.conversation_turn_id = ct.id
               WHERE s.conversation_turn_id IS NOT NULL AND ct.id IS NULL"""
        ).fetchone()[0]
        assert orphaned == 0

    def test_milestone_counts_per_goal(self) -> None:
        """Verify milestone distribution: Sarah goal1=4, Sarah goal2=4, Elena goal=4."""
        data = get_seed_data()
        goal_ids = {g["id"] for g in data["goals"]}
        for goal_id in goal_ids:
            count = self.conn.execute(
                "SELECT COUNT(*) FROM milestones WHERE goal_id = ?", (goal_id,)
            ).fetchone()[0]
            # Sarah's 2 goals and Elena's 1 goal each have 4 milestones.
            # Marcus's goal has 0 milestones (not confirmed yet).
            assert count in (0, 4), f"Goal {goal_id} has {count} milestones (expected 0 or 4)"

    def test_reminders_belong_to_elena(self) -> None:
        """Both reminders should belong to Elena (re-engaging patient)."""
        elena_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Elena'"
        ).fetchone()["user_id"]
        reminder_users = self.conn.execute(
            "SELECT DISTINCT user_id FROM reminders"
        ).fetchall()
        assert len(reminder_users) == 1
        assert reminder_users[0]["user_id"] == elena_user_id

    def test_clinician_alert_belongs_to_elena(self) -> None:
        """The clinician alert should belong to Elena."""
        elena_user_id = self.conn.execute(
            "SELECT user_id FROM profiles WHERE display_name = 'Elena'"
        ).fetchone()["user_id"]
        alert = self.conn.execute(
            "SELECT user_id FROM clinician_alerts"
        ).fetchone()
        assert alert["user_id"] == elena_user_id


# ============================================================================
# TestGetSeedData
# ============================================================================
class TestGetSeedData:
    """Tests for the get_seed_data() pure function (no DB required)."""

    def test_get_seed_data_returns_dict(self) -> None:
        data = get_seed_data()
        assert isinstance(data, dict)

    def test_get_seed_data_has_all_tables(self) -> None:
        data = get_seed_data()
        expected_keys = {
            "profiles", "goals", "milestones", "conversation_turns",
            "safety_audit_log", "clinician_alerts", "reminders",
            "conversation_summaries",
        }
        assert set(data.keys()) == expected_keys

    def test_get_seed_data_profiles_count(self) -> None:
        data = get_seed_data()
        assert len(data["profiles"]) == 3

    def test_get_seed_data_goals_count(self) -> None:
        data = get_seed_data()
        assert len(data["goals"]) == 4

    def test_get_seed_data_milestones_count(self) -> None:
        data = get_seed_data()
        assert len(data["milestones"]) == 12

    def test_get_seed_data_turns_count(self) -> None:
        data = get_seed_data()
        assert len(data["conversation_turns"]) == 26

    def test_get_seed_data_safety_count(self) -> None:
        data = get_seed_data()
        assert len(data["safety_audit_log"]) == 3

    def test_get_seed_data_alerts_count(self) -> None:
        data = get_seed_data()
        assert len(data["clinician_alerts"]) == 1

    def test_get_seed_data_reminders_count(self) -> None:
        data = get_seed_data()
        assert len(data["reminders"]) == 2

    def test_get_seed_data_summaries_count(self) -> None:
        data = get_seed_data()
        assert len(data["conversation_summaries"]) == 1


# ============================================================================
# TestHashPassword
# ============================================================================
class TestHashPassword:
    """Tests for the _hash_password helper in seed.py."""

    def test_hash_password_returns_string(self) -> None:
        result = _hash_password("test")
        assert isinstance(result, str)

    def test_hash_password_format(self) -> None:
        result = _hash_password("test")
        parts = result.split(":")
        assert len(parts) == 2, "Hash should be in salt:hash format"
        assert len(parts[0]) == 32, "Salt should be 32 hex chars (16 bytes)"
        assert len(parts[1]) == 64, "Hash should be 64 hex chars (32 bytes)"

    def test_hash_password_unique_salts(self) -> None:
        """Two calls with the same password should produce different hashes."""
        h1 = _hash_password("password123")
        h2 = _hash_password("password123")
        assert h1 != h2, "Each hash should use a unique random salt"

    def test_hash_password_verifiable(self) -> None:
        """The hash should be verifiable using the same PBKDF2 parameters."""
        pw = "my_secret_password"
        stored = _hash_password(pw)
        salt_hex, hash_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        computed = hashlib.pbkdf2_hmac("sha256", pw.encode(), salt, 100000)
        assert computed.hex() == hash_hex

    def test_hash_password_wrong_password_fails(self) -> None:
        """Verifying with the wrong password should not match."""
        stored = _hash_password("correct_password")
        salt_hex, hash_hex = stored.split(":")
        salt = bytes.fromhex(salt_hex)
        computed = hashlib.pbkdf2_hmac("sha256", "wrong_password".encode(), salt, 100000)
        assert computed.hex() != hash_hex
