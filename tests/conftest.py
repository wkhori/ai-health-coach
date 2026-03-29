"""Shared fixtures for all test modules."""

import sqlite3
from unittest.mock import MagicMock
from uuid import UUID, uuid4

import pytest

from src.db.schema import init_db

# A fixed user_id for testing
TEST_USER_ID = UUID("00000000-0000-0000-0000-000000000001")
TEST_GOAL_ID = UUID("00000000-0000-0000-0000-000000000002")
TEST_ALERT_ID = UUID("00000000-0000-0000-0000-000000000003")


@pytest.fixture
def user_id() -> UUID:
    return TEST_USER_ID


@pytest.fixture
def goal_id() -> UUID:
    return TEST_GOAL_ID


@pytest.fixture
def db_conn() -> sqlite3.Connection:
    """An in-memory SQLite connection with all tables created."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    init_db(conn)
    return conn


@pytest.fixture
def mock_alert_repo() -> MagicMock:
    """Mock AlertRepository."""
    repo = MagicMock()
    repo.create.return_value = {
        "id": str(uuid4()),
        "user_id": str(TEST_USER_ID),
        "alert_type": "crisis",
        "urgency": "urgent",
        "status": "pending",
        "message": "Test alert",
    }
    return repo
