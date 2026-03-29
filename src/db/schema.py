"""SQLite schema definitions and initialization for the AI Health Coach database."""

import sqlite3

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS profiles (
    id TEXT PRIMARY KEY,
    user_id TEXT UNIQUE NOT NULL,
    display_name TEXT,
    timezone TEXT DEFAULT 'UTC',
    phase TEXT DEFAULT 'PENDING' CHECK (phase IN ('PENDING', 'ONBOARDING', 'ACTIVE', 'RE_ENGAGING', 'DORMANT')),
    phase_updated_at TEXT,
    consent_given_at TEXT,
    consent_revoked_at TEXT,
    consent_version TEXT,
    onboarding_completed_at TEXT,
    last_message_at TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS goals (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    frequency TEXT DEFAULT '',
    target_per_week INTEGER DEFAULT 0,
    confirmed BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed')),
    target_date TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    updated_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS milestones (
    id TEXT PRIMARY KEY,
    goal_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT DEFAULT '',
    week_number INTEGER NOT NULL,
    completed BOOLEAN DEFAULT 0,
    completed_at TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (goal_id) REFERENCES goals(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS reminders (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    reminder_type TEXT NOT NULL,
    message_template TEXT DEFAULT '',
    scheduled_at TEXT,
    due_at TEXT,
    sent_at TEXT,
    status TEXT DEFAULT 'pending',
    retry_count INTEGER DEFAULT 0,
    attempt_number INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS conversation_turns (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    phase TEXT,
    turn_number INTEGER,
    tool_calls TEXT,
    tool_results TEXT,
    token_count_input INTEGER,
    token_count_output INTEGER,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS safety_audit_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    conversation_turn_id TEXT,
    input_text TEXT,
    classification TEXT,
    confidence REAL,
    categories TEXT,
    flagged_phrases TEXT,
    reasoning TEXT,
    action_taken TEXT,
    tier TEXT,
    model_used TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (conversation_turn_id) REFERENCES conversation_turns(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS clinician_alerts (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    safety_audit_id TEXT,
    alert_type TEXT,
    urgency TEXT DEFAULT 'routine',
    status TEXT DEFAULT 'pending',
    message TEXT,
    acknowledged_at TEXT,
    notes TEXT,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (safety_audit_id) REFERENCES safety_audit_log(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS conversation_summaries (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    summary_text TEXT,
    turns_covered_from INTEGER,
    turns_covered_to INTEGER,
    created_at TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ', 'now')),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Trigger to auto-update updated_at on profiles
CREATE TRIGGER IF NOT EXISTS profiles_updated_at
    AFTER UPDATE ON profiles
    FOR EACH ROW
BEGIN
    UPDATE profiles SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = OLD.id;
END;

-- Trigger to auto-update updated_at on goals
CREATE TRIGGER IF NOT EXISTS goals_updated_at
    AFTER UPDATE ON goals
    FOR EACH ROW
BEGIN
    UPDATE goals SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ', 'now')
    WHERE id = OLD.id;
END;
"""


def init_db(conn: sqlite3.Connection) -> None:
    """Initialize the database schema. Creates all tables if they don't exist and enables WAL mode."""
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
