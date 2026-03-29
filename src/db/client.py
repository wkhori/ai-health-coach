import sqlite3
from pathlib import Path

from src.db.schema import init_db

_connection: sqlite3.Connection | None = None


def get_db(db_path: str = "health_coach.db") -> sqlite3.Connection:
    """Get or create a shared SQLite connection."""
    global _connection
    if _connection is None:
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        _connection = sqlite3.connect(str(path), check_same_thread=False)
        _connection.row_factory = sqlite3.Row
        _connection.execute("PRAGMA journal_mode=WAL")
        _connection.execute("PRAGMA foreign_keys=ON")
        init_db(_connection)
    return _connection


def reset_db() -> None:
    """Close and clear the cached connection (for testing)."""
    global _connection
    if _connection is not None:
        _connection.close()
        _connection = None
