"""Seed data script for demo purposes — no real Supabase connection required.

Defines 3 test patients at different lifecycle stages with realistic
conversation content, safety audit entries, clinician alerts, and reminders.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta
from typing import TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    import sqlite3

import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Fixed UUIDs for reproducibility
# ---------------------------------------------------------------------------
_SARAH_USER_ID = UUID("10000000-0000-0000-0000-000000000001")
_SARAH_PROFILE_ID = UUID("20000000-0000-0000-0000-000000000001")
_SARAH_GOAL_1_ID = UUID("30000000-0000-0000-0000-000000000001")
_SARAH_GOAL_2_ID = UUID("30000000-0000-0000-0000-000000000002")

_MARCUS_USER_ID = UUID("10000000-0000-0000-0000-000000000002")
_MARCUS_PROFILE_ID = UUID("20000000-0000-0000-0000-000000000002")
_MARCUS_GOAL_ID = UUID("30000000-0000-0000-0000-000000000003")

_ELENA_USER_ID = UUID("10000000-0000-0000-0000-000000000003")
_ELENA_PROFILE_ID = UUID("20000000-0000-0000-0000-000000000003")
_ELENA_GOAL_ID = UUID("30000000-0000-0000-0000-000000000004")

_SAFETY_AUDIT_1_ID = UUID("40000000-0000-0000-0000-000000000001")
_SAFETY_AUDIT_2_ID = UUID("40000000-0000-0000-0000-000000000002")
_SAFETY_AUDIT_3_ID = UUID("40000000-0000-0000-0000-000000000003")

_ALERT_1_ID = UUID("50000000-0000-0000-0000-000000000001")

_REMINDER_1_ID = UUID("60000000-0000-0000-0000-000000000001")
_REMINDER_2_ID = UUID("60000000-0000-0000-0000-000000000002")

_TURN_ID_BASE = UUID("70000000-0000-0000-0000-000000000000")

# ---------------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------------
_NOW = datetime(2026, 3, 27, 10, 0, 0)
_DAY = timedelta(days=1)
_HOUR = timedelta(hours=1)


def _turn_id(n: int) -> str:
    """Generate a deterministic turn UUID from an index."""
    return str(UUID(int=_TURN_ID_BASE.int + n))


# ---------------------------------------------------------------------------
# Profiles
# ---------------------------------------------------------------------------
def _profiles() -> list[dict]:
    return [
        {
            "id": str(_SARAH_PROFILE_ID),
            "user_id": str(_SARAH_USER_ID),
            "display_name": "Sarah",
            "timezone": "America/New_York",
            "phase": "ACTIVE",
            "phase_updated_at": (_NOW - 10 * _DAY).isoformat(),
            "consent_given_at": (_NOW - 14 * _DAY).isoformat(),
            "consent_revoked_at": None,
            "consent_version": "1.0",
            "onboarding_completed_at": (_NOW - 12 * _DAY).isoformat(),
            "last_message_at": (_NOW - 2 * _HOUR).isoformat(),
            "created_at": (_NOW - 14 * _DAY).isoformat(),
            "updated_at": (_NOW - 2 * _HOUR).isoformat(),
        },
        {
            "id": str(_MARCUS_PROFILE_ID),
            "user_id": str(_MARCUS_USER_ID),
            "display_name": "Marcus",
            "timezone": "America/Chicago",
            "phase": "ONBOARDING",
            "phase_updated_at": (_NOW - 1 * _DAY).isoformat(),
            "consent_given_at": (_NOW - 1 * _DAY).isoformat(),
            "consent_revoked_at": None,
            "consent_version": "1.0",
            "onboarding_completed_at": None,
            "last_message_at": (_NOW - 3 * _HOUR).isoformat(),
            "created_at": (_NOW - 1 * _DAY).isoformat(),
            "updated_at": (_NOW - 3 * _HOUR).isoformat(),
        },
        {
            "id": str(_ELENA_PROFILE_ID),
            "user_id": str(_ELENA_USER_ID),
            "display_name": "Elena",
            "timezone": "America/Los_Angeles",
            "phase": "RE_ENGAGING",
            "phase_updated_at": (_NOW - 3 * _DAY).isoformat(),
            "consent_given_at": (_NOW - 20 * _DAY).isoformat(),
            "consent_revoked_at": None,
            "consent_version": "1.0",
            "onboarding_completed_at": (_NOW - 18 * _DAY).isoformat(),
            "last_message_at": (_NOW - 5 * _DAY).isoformat(),
            "created_at": (_NOW - 20 * _DAY).isoformat(),
            "updated_at": (_NOW - 5 * _DAY).isoformat(),
        },
    ]


# ---------------------------------------------------------------------------
# Goals
# ---------------------------------------------------------------------------
def _goals() -> list[dict]:
    return [
        # Sarah: 2 confirmed goals
        {
            "id": str(_SARAH_GOAL_1_ID),
            "user_id": str(_SARAH_USER_ID),
            "title": "Walk 30 minutes daily",
            "description": "Build a consistent daily walking habit starting with 20 min and working up to 30 min.",
            "frequency": "daily",
            "target_per_week": 7,
            "confirmed": True,
            "status": "active",
            "target_date": (_NOW + 14 * _DAY).strftime("%Y-%m-%d"),
            "created_at": (_NOW - 12 * _DAY).isoformat(),
            "updated_at": (_NOW - 2 * _HOUR).isoformat(),
        },
        {
            "id": str(_SARAH_GOAL_2_ID),
            "user_id": str(_SARAH_USER_ID),
            "title": "Strengthen upper body 3x/week",
            "description": "Resistance band exercises focusing on shoulders, arms, and back. 3 sessions per week.",
            "frequency": "3 times per week",
            "target_per_week": 3,
            "confirmed": True,
            "status": "active",
            "target_date": (_NOW + 14 * _DAY).strftime("%Y-%m-%d"),
            "created_at": (_NOW - 10 * _DAY).isoformat(),
            "updated_at": (_NOW - 1 * _DAY).isoformat(),
        },
        # Marcus: 1 goal, NOT confirmed
        {
            "id": str(_MARCUS_GOAL_ID),
            "user_id": str(_MARCUS_USER_ID),
            "title": "Start jogging",
            "description": "Begin a couch-to-5K program, building endurance over 8 weeks.",
            "frequency": "3 times per week",
            "target_per_week": 3,
            "confirmed": False,
            "status": "active",
            "target_date": None,
            "created_at": (_NOW - 3 * _HOUR).isoformat(),
            "updated_at": (_NOW - 3 * _HOUR).isoformat(),
        },
        # Elena: 1 confirmed goal
        {
            "id": str(_ELENA_GOAL_ID),
            "user_id": str(_ELENA_USER_ID),
            "title": "Yoga flexibility routine",
            "description": "Daily 15-minute yoga flow for hip and hamstring flexibility.",
            "frequency": "daily",
            "target_per_week": 5,
            "confirmed": True,
            "status": "active",
            "target_date": (_NOW + 7 * _DAY).strftime("%Y-%m-%d"),
            "created_at": (_NOW - 18 * _DAY).isoformat(),
            "updated_at": (_NOW - 5 * _DAY).isoformat(),
        },
    ]


# ---------------------------------------------------------------------------
# Milestones
# ---------------------------------------------------------------------------
def _milestones() -> list[dict]:
    ms = []
    # Sarah Goal 1: 4 milestones, 2 completed
    sarah_g1_ms = [
        ("Walk 20 min, 5 days", True, _NOW - 10 * _DAY),
        ("Walk 25 min, 6 days", True, _NOW - 5 * _DAY),
        ("Walk 30 min, 7 days", False, None),
        ("Maintain 30 min streak for a full week", False, None),
    ]
    for i, (title, completed, completed_at) in enumerate(sarah_g1_ms, start=1):
        ms.append(
            {
                "id": _turn_id(800 + i),
                "goal_id": str(_SARAH_GOAL_1_ID),
                "user_id": str(_SARAH_USER_ID),
                "title": title,
                "description": f"Week {i} milestone for walking goal",
                "week_number": i,
                "completed": completed,
                "completed_at": completed_at.isoformat() if completed_at else None,
                "created_at": (_NOW - 12 * _DAY).isoformat(),
            }
        )

    # Sarah Goal 2: 4 milestones, 1 completed
    sarah_g2_ms = [
        ("2 sessions of 15 min each", True, _NOW - 7 * _DAY),
        ("3 sessions of 20 min each", False, None),
        ("3 sessions of 25 min each", False, None),
        ("3 sessions of 30 min with heavier bands", False, None),
    ]
    for i, (title, completed, completed_at) in enumerate(sarah_g2_ms, start=1):
        ms.append(
            {
                "id": _turn_id(810 + i),
                "goal_id": str(_SARAH_GOAL_2_ID),
                "user_id": str(_SARAH_USER_ID),
                "title": title,
                "description": f"Week {i} milestone for upper body goal",
                "week_number": i,
                "completed": completed,
                "completed_at": completed_at.isoformat() if completed_at else None,
                "created_at": (_NOW - 10 * _DAY).isoformat(),
            }
        )

    # Elena Goal: 4 milestones, 1 completed
    elena_ms = [
        ("Complete 5 yoga sessions", True, _NOW - 14 * _DAY),
        ("Hold each stretch for 45 seconds", False, None),
        ("Add hip-opener sequence", False, None),
        ("Full 20-minute flow without breaks", False, None),
    ]
    for i, (title, completed, completed_at) in enumerate(elena_ms, start=1):
        ms.append(
            {
                "id": _turn_id(820 + i),
                "goal_id": str(_ELENA_GOAL_ID),
                "user_id": str(_ELENA_USER_ID),
                "title": title,
                "description": f"Week {i} milestone for yoga goal",
                "week_number": i,
                "completed": completed,
                "completed_at": completed_at.isoformat() if completed_at else None,
                "created_at": (_NOW - 18 * _DAY).isoformat(),
            }
        )

    return ms


# ---------------------------------------------------------------------------
# Conversation turns
# ---------------------------------------------------------------------------
def _conversation_turns() -> list[dict]:
    turns: list[dict] = []
    n = 0

    # --- Sarah: 15 turns (ACTIVE phase, good adherence) ---
    sarah_convo = [
        ("user", "Hi, I'd like to start exercising more regularly.", "ONBOARDING"),
        (
            "assistant",
            "Welcome, Sarah! I'm excited to help you build an exercise routine. What kind of activities do you enjoy?",
            "ONBOARDING",
        ),
        ("user", "I like walking and I used to do resistance training.", "ONBOARDING"),
        (
            "assistant",
            "That's great! Walking and resistance training are excellent foundations. Let's set your first goal. How about we start with daily walks?",
            "ONBOARDING",
        ),
        (
            "user",
            "Yes! I want to walk 30 minutes every day.",
            "ONBOARDING",
        ),
        (
            "assistant",
            "Your goal has been set! Walk 30 minutes daily. Here's your 4-week plan:\n- Week 1: Walk 20 min, 5 days\n- Week 2: Walk 25 min, 6 days\n- Week 3: Walk 30 min, 7 days\n- Week 4: Maintain 30 min streak\nI'll help you track progress each week!",
            "ONBOARDING",
        ),
        (
            "user",
            "I also want to add upper body strengthening.",
            "ACTIVE",
        ),
        (
            "assistant",
            "Great idea, Sarah! Let's set up your upper body goal. I'll create a plan with resistance band exercises 3 times per week.",
            "ACTIVE",
        ),
        (
            "user",
            "I did my walk and my arm exercises today!",
            "ACTIVE",
        ),
        (
            "assistant",
            "Amazing work! Keep it up! You're building such great momentum. Your walking streak is now at 5 days. How did the resistance bands feel?",
            "ACTIVE",
        ),
        (
            "user",
            "The bands felt good but my shoulders were a bit sore afterward.",
            "ACTIVE",
        ),
        (
            "assistant",
            "Some mild soreness after resistance training is normal, especially when starting out. Make sure you're doing gentle stretches afterward. If the soreness persists or gets worse, please check in with your care team.",
            "ACTIVE",
        ),
        (
            "user",
            "Thanks! I completed my Week 1 milestones for both goals.",
            "ACTIVE",
        ),
        (
            "assistant",
            "Well done on completing your first week milestones! That's a huge accomplishment. You're 25% through your plan already. Ready to tackle Week 2?",
            "ACTIVE",
        ),
        (
            "user",
            "Absolutely! Feeling motivated.",
            "ACTIVE",
        ),
    ]
    for role, content, phase in sarah_convo:
        n += 1
        tool_calls = None
        if "goal has been set" in content.lower():
            tool_calls = {"name": "set_goal", "args": {"title": "Walk 30 minutes daily"}}
        turns.append(
            {
                "id": _turn_id(n),
                "user_id": str(_SARAH_USER_ID),
                "role": role,
                "content": content,
                "phase": phase,
                "tool_calls": tool_calls,
                "tool_results": None,
                "token_count_input": 150 if role == "user" else None,
                "token_count_output": 200 if role == "assistant" else None,
                "turn_number": n,
                "created_at": (_NOW - 14 * _DAY + n * _HOUR).isoformat(),
            }
        )

    # --- Marcus: 3 turns (ONBOARDING phase) ---
    marcus_convo = [
        ("user", "Hey, I just signed up. What can you help me with?", "ONBOARDING"),
        (
            "assistant",
            "Welcome, Marcus! I'm your wellness coach. I'm here to help you set exercise goals and stay on track. What kind of physical activity are you interested in?",
            "ONBOARDING",
        ),
        (
            "user",
            "I want to start jogging but I've never really run before.",
            "ONBOARDING",
        ),
    ]
    for role, content, phase in marcus_convo:
        n += 1
        turns.append(
            {
                "id": _turn_id(n),
                "user_id": str(_MARCUS_USER_ID),
                "role": role,
                "content": content,
                "phase": phase,
                "tool_calls": None,
                "tool_results": None,
                "token_count_input": 100 if role == "user" else None,
                "token_count_output": 180 if role == "assistant" else None,
                "turn_number": n - 15,
                "created_at": (_NOW - 1 * _DAY + (n - 15) * _HOUR).isoformat(),
            }
        )

    # --- Elena: 8 turns (RE_ENGAGING phase, last message 5 days ago) ---
    elena_convo = [
        ("user", "I'd like to work on my flexibility.", "ONBOARDING"),
        (
            "assistant",
            "Great choice, Elena! Flexibility training can make a big difference. Would you like to try a daily yoga routine?",
            "ONBOARDING",
        ),
        ("user", "Yes, yoga sounds perfect. 15 minutes a day.", "ONBOARDING"),
        (
            "assistant",
            "Your goal has been set! Daily yoga flexibility routine, 15 minutes a day. Here's your plan:\n- Week 1: Complete 5 yoga sessions\n- Week 2: Hold each stretch for 45 seconds\n- Week 3: Add hip-opener sequence\n- Week 4: Full 20-minute flow",
            "ONBOARDING",
        ),
        (
            "user",
            "I did yoga every day this week! Feeling great.",
            "ACTIVE",
        ),
        (
            "assistant",
            "Incredible dedication, Elena! Five sessions in your first week is exactly what we were aiming for. You've completed your Week 1 milestone. How does your body feel?",
            "ACTIVE",
        ),
        (
            "user",
            "Really good, but I've been busy this week and missed a few sessions.",
            "ACTIVE",
        ),
        (
            "assistant",
            "That's completely okay! Life gets busy sometimes. The important thing is that you built a strong foundation in Week 1. Let's see how we can fit in shorter sessions on your busy days. Even 5 minutes of stretching counts!",
            "ACTIVE",
        ),
    ]
    for role, content, phase in elena_convo:
        n += 1
        tool_calls = None
        if "goal has been set" in content.lower():
            tool_calls = {"name": "set_goal", "args": {"title": "Yoga flexibility routine"}}
        turns.append(
            {
                "id": _turn_id(n),
                "user_id": str(_ELENA_USER_ID),
                "role": role,
                "content": content,
                "phase": phase,
                "tool_calls": tool_calls,
                "tool_results": None,
                "token_count_input": 120 if role == "user" else None,
                "token_count_output": 190 if role == "assistant" else None,
                "turn_number": n - 18,
                "created_at": (_NOW - 20 * _DAY + (n - 18) * _HOUR).isoformat(),
            }
        )

    return turns


# ---------------------------------------------------------------------------
# Safety audit entries
# ---------------------------------------------------------------------------
def _safety_audit_log() -> list[dict]:
    return [
        # Entry 1: Sarah's message passed safety check
        {
            "id": str(_SAFETY_AUDIT_1_ID),
            "user_id": str(_SARAH_USER_ID),
            "conversation_turn_id": _turn_id(10),
            "input_text": "Amazing work! Keep it up! You're building such great momentum.",
            "classification": "safe",
            "confidence": 0.99,
            "categories": ["positive_reinforcement"],
            "flagged_phrases": [],
            "reasoning": "Tier 1 rule: positive reinforcement pattern matched",
            "action_taken": "passed",
            "tier": "rule",
            "model_used": "",
            "created_at": (_NOW - 8 * _DAY).isoformat(),
        },
        # Entry 2: Sarah's soreness response passed (Tier 2)
        {
            "id": str(_SAFETY_AUDIT_2_ID),
            "user_id": str(_SARAH_USER_ID),
            "conversation_turn_id": _turn_id(12),
            "input_text": "Some mild soreness after resistance training is normal, especially when starting out.",
            "classification": "safe",
            "confidence": 0.87,
            "categories": ["general_wellness"],
            "flagged_phrases": [],
            "reasoning": "General wellness advice about post-exercise soreness. No clinical claims.",
            "action_taken": "passed",
            "tier": "llm",
            "model_used": "claude-haiku-4-5-20251001",
            "created_at": (_NOW - 7 * _DAY).isoformat(),
        },
        # Entry 3: Flagged as clinical -> rewritten
        {
            "id": str(_SAFETY_AUDIT_3_ID),
            "user_id": str(_SARAH_USER_ID),
            "conversation_turn_id": _turn_id(12),
            "input_text": "You should take 400 mg of ibuprofen for the muscle soreness.",
            "classification": "clinical",
            "confidence": 0.95,
            "categories": ["dosage"],
            "flagged_phrases": ["400 mg"],
            "reasoning": "Tier 1 rule: dosage pattern matched - '400 mg'",
            "action_taken": "rewritten",
            "tier": "rule",
            "model_used": "",
            "created_at": (_NOW - 7 * _DAY).isoformat(),
        },
    ]


# ---------------------------------------------------------------------------
# Clinician alerts
# ---------------------------------------------------------------------------
def _clinician_alerts() -> list[dict]:
    return [
        {
            "id": str(_ALERT_1_ID),
            "user_id": str(_ELENA_USER_ID),
            "safety_audit_id": None,
            "alert_type": "disengagement",
            "urgency": "routine",
            "status": "pending",
            "message": "Patient Elena has not responded for 5 days. Re-engagement attempt 1 (Day 2) was sent but received no reply.",
            "acknowledged_at": None,
            "notes": None,
            "created_at": (_NOW - 3 * _DAY).isoformat(),
        },
    ]


# ---------------------------------------------------------------------------
# Reminders
# ---------------------------------------------------------------------------
def _reminders() -> list[dict]:
    return [
        # Elena Day 2 reminder — sent
        {
            "id": str(_REMINDER_1_ID),
            "user_id": str(_ELENA_USER_ID),
            "reminder_type": "follow_up",
            "message_template": "Re-engagement attempt 1",
            "scheduled_at": (_NOW - 3 * _DAY).isoformat(),
            "due_at": (_NOW - 3 * _DAY).isoformat(),
            "sent_at": (_NOW - 3 * _DAY).isoformat(),
            "status": "sent",
            "retry_count": 0,
            "attempt_number": 1,
            "created_at": (_NOW - 5 * _DAY).isoformat(),
        },
        # Elena Day 5 reminder — pending
        {
            "id": str(_REMINDER_2_ID),
            "user_id": str(_ELENA_USER_ID),
            "reminder_type": "follow_up",
            "message_template": "Re-engagement attempt 2",
            "scheduled_at": _NOW.isoformat(),
            "due_at": _NOW.isoformat(),
            "sent_at": None,
            "status": "pending",
            "retry_count": 0,
            "attempt_number": 2,
            "created_at": (_NOW - 5 * _DAY).isoformat(),
        },
    ]


# ---------------------------------------------------------------------------
# Conversation summaries
# ---------------------------------------------------------------------------
def _conversation_summaries() -> list[dict]:
    return [
        {
            "id": _turn_id(900),
            "user_id": str(_SARAH_USER_ID),
            "summary_text": (
                "Sarah is an engaged patient working on two goals: daily 30-minute walks and "
                "upper body resistance training 3x/week. She completed Week 1 milestones for both "
                "goals and experienced mild post-exercise soreness (normal). She reports feeling "
                "motivated and is ready for Week 2. No barriers identified."
            ),
            "turns_covered_from": 1,
            "turns_covered_to": 12,
            "created_at": (_NOW - 3 * _DAY).isoformat(),
        },
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_seed_data() -> dict:
    """Return all seed data organized by table name.

    Returns a dictionary with table names as keys and lists of row dicts as values.
    No database connection is required.
    """
    return {
        "profiles": _profiles(),
        "goals": _goals(),
        "milestones": _milestones(),
        "conversation_turns": _conversation_turns(),
        "safety_audit_log": _safety_audit_log(),
        "clinician_alerts": _clinician_alerts(),
        "reminders": _reminders(),
        "conversation_summaries": _conversation_summaries(),
    }


def print_summary(data: dict | None = None) -> None:
    """Print a human-readable summary of the seed data."""
    if data is None:
        data = get_seed_data()

    logger.info("seed_data_summary")
    print("\n=== AI Health Coach — Seed Data Summary ===\n")  # noqa: T201

    for table, rows in data.items():
        print(f"  {table}: {len(rows)} rows")  # noqa: T201

    print("\n--- Patients ---")  # noqa: T201
    for p in data["profiles"]:
        goal_count = sum(1 for g in data["goals"] if g["user_id"] == p["user_id"])
        ms_count = sum(1 for m in data["milestones"] if m["user_id"] == p["user_id"])
        ms_done = sum(
            1 for m in data["milestones"] if m["user_id"] == p["user_id"] and m["completed"]
        )
        turn_count = sum(1 for t in data["conversation_turns"] if t["user_id"] == p["user_id"])
        print(  # noqa: T201
            f"  {p['display_name']:10s} | phase={p['phase']:15s} | "
            f"goals={goal_count} | milestones={ms_done}/{ms_count} | turns={turn_count}"
        )

    alert_count = len(data["clinician_alerts"])
    audit_flagged = sum(1 for a in data["safety_audit_log"] if a["action_taken"] != "passed")
    audit_passed = sum(1 for a in data["safety_audit_log"] if a["action_taken"] == "passed")
    reminder_sent = sum(1 for r in data["reminders"] if r["status"] == "sent")
    reminder_pending = sum(1 for r in data["reminders"] if r["status"] == "pending")

    print("\n--- Safety ---")  # noqa: T201
    print(
        f"  Audit entries: {len(data['safety_audit_log'])} ({audit_passed} passed, {audit_flagged} flagged)"
    )  # noqa: T201
    print(f"  Clinician alerts: {alert_count}")  # noqa: T201

    print("\n--- Reminders ---")  # noqa: T201
    print(f"  Total: {len(data['reminders'])} ({reminder_sent} sent, {reminder_pending} pending)")  # noqa: T201
    print()  # noqa: T201


# ---------------------------------------------------------------------------
# Password hashing for demo users
# ---------------------------------------------------------------------------
def _hash_password(password: str) -> str:
    """Hash a password with a random salt using PBKDF2."""
    salt = os.urandom(16)
    hash_bytes = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + hash_bytes.hex()


# ---------------------------------------------------------------------------
# SQLite seeding
# ---------------------------------------------------------------------------

# Table -> ordered column list (must match the seed data dict keys)
_TABLE_COLUMNS: dict[str, list[str]] = {
    "profiles": [
        "id", "user_id", "display_name", "timezone", "phase", "phase_updated_at",
        "consent_given_at", "consent_revoked_at", "consent_version",
        "onboarding_completed_at", "last_message_at", "created_at", "updated_at",
    ],
    "goals": [
        "id", "user_id", "title", "description", "frequency", "target_per_week",
        "confirmed", "status", "target_date", "created_at", "updated_at",
    ],
    "milestones": [
        "id", "goal_id", "user_id", "title", "description", "week_number",
        "completed", "completed_at", "created_at",
    ],
    "conversation_turns": [
        "id", "user_id", "role", "content", "phase", "tool_calls", "tool_results",
        "token_count_input", "token_count_output", "turn_number", "created_at",
    ],
    "safety_audit_log": [
        "id", "user_id", "conversation_turn_id", "input_text", "classification",
        "confidence", "categories", "flagged_phrases", "reasoning", "action_taken",
        "tier", "model_used", "created_at",
    ],
    "clinician_alerts": [
        "id", "user_id", "safety_audit_id", "alert_type", "urgency", "status",
        "message", "acknowledged_at", "notes", "created_at",
    ],
    "reminders": [
        "id", "user_id", "reminder_type", "message_template", "scheduled_at",
        "due_at", "sent_at", "status", "retry_count", "attempt_number", "created_at",
    ],
    "conversation_summaries": [
        "id", "user_id", "summary_text", "turns_covered_from", "turns_covered_to",
        "created_at",
    ],
}


def _serialize_value(value: object) -> object:
    """Serialize a Python value for SQLite insertion.

    Converts dicts/lists to JSON strings, booleans to integers, and
    passes through everything else (str, int, float, None).
    """
    if isinstance(value, dict | list):
        return json.dumps(value)
    if isinstance(value, bool):
        return int(value)
    return value


def seed_db(conn: sqlite3.Connection) -> None:
    """Seed the SQLite database with demo data.

    Creates 3 demo users in the users table, then inserts all seed data
    into their respective tables.
    """
    # 1. Create demo users
    demo_users = [
        (str(_SARAH_USER_ID), "sarah@demo.com", _hash_password("password123")),
        (str(_MARCUS_USER_ID), "marcus@demo.com", _hash_password("password123")),
        (str(_ELENA_USER_ID), "elena@demo.com", _hash_password("password123")),
    ]
    for user_id, email, pw_hash in demo_users:
        conn.execute(
            "INSERT OR IGNORE INTO users (id, email, password_hash) VALUES (?, ?, ?)",
            (user_id, email, pw_hash),
        )

    # 2. Insert all seed data
    data = get_seed_data()

    for table_name, rows in data.items():
        columns = _TABLE_COLUMNS[table_name]
        placeholders = ", ".join("?" for _ in columns)
        col_names = ", ".join(columns)
        sql = f"INSERT OR IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})"

        for row in rows:
            values = tuple(_serialize_value(row.get(col)) for col in columns)
            conn.execute(sql, values)

    conn.commit()
    logger.info("seed_db_complete", tables=list(data.keys()), user_count=len(demo_users))


# ---------------------------------------------------------------------------
# CLI entry point: python -m src.db.seed
# ---------------------------------------------------------------------------
def _cli_main() -> None:
    """CLI entry point that seeds the database and prints summary."""
    from src.db.client import get_db

    conn = get_db()
    seed_db(conn)
    print_summary()

    if "--json" in sys.argv:
        # Also dump the raw data as JSON for inspection
        data = get_seed_data()

        def _default(o: object) -> str:
            if isinstance(o, datetime):
                return o.isoformat()
            if isinstance(o, UUID):
                return str(o)
            return str(o)

        print(json.dumps(data, indent=2, default=_default))  # noqa: T201


if __name__ == "__main__":
    _cli_main()
