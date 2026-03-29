"""Tests for FastAPI endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.main import (
    _rate_limit_store,
    app,
    check_rate_limit,
    get_current_user,
)

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"
TEST_PROFILE_ID = "00000000-0000-0000-0000-000000000099"


# Override auth for testing
async def mock_get_current_user():
    return {"user_id": TEST_USER_ID}


app.dependency_overrides[get_current_user] = mock_get_current_user


@pytest.fixture(autouse=True)
def clear_rate_limits():
    """Clear rate limit store between tests."""
    _rate_limit_store.clear()
    yield
    _rate_limit_store.clear()


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_profile_repo():
    repo = MagicMock()
    repo.get_by_user_id.return_value = {
        "id": TEST_PROFILE_ID,
        "user_id": TEST_USER_ID,
        "display_name": "Test Patient",
        "phase": "ONBOARDING",
        "consent_given_at": "2024-01-01T00:00:00",
        "consent_revoked_at": None,
    }
    return repo


@pytest.fixture
def mock_goal_repo():
    repo = MagicMock()
    repo.get_by_user.return_value = [
        {
            "id": str(uuid4()),
            "title": "Walk daily",
            "confirmed": True,
            "milestones": [],
        }
    ]
    return repo


@pytest.fixture
def mock_conversation_repo():
    repo = MagicMock()
    repo.get_recent_turns.return_value = [
        {"role": "user", "content": "hello", "turn_number": 1},
        {"role": "assistant", "content": "hi!", "turn_number": 2},
    ]
    repo.get_turn_count.return_value = 2
    return repo


class TestHealthCheck:
    """Tests for /api/health endpoint."""

    def test_health_returns_200(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200

    def test_health_returns_status(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_returns_timestamp(self, client):
        response = client.get("/api/health")
        data = response.json()
        assert "timestamp" in data


class TestChatSync:
    """Tests for /api/chat/sync endpoint."""

    def test_chat_sync_returns_response(self, client):
        """Sync chat returns a ChatResponse."""
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "response_text": "Hello! How can I help?",
            "phase": "ONBOARDING",
            "safety_result": {"classification": "safe", "action": "passed"},
        }

        with patch("src.main.get_graph", return_value=mock_graph):
            response = client.post(
                "/api/chat/sync",
                json={"message": "hello"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["response"] == "Hello! How can I help?"
        assert data["phase"] == "ONBOARDING"


class TestConsent:
    """Tests for /api/consent endpoint."""

    def test_consent_requires_profile(self, client):
        """Returns 503 when repos not configured."""
        with patch("src.main.get_repos", return_value={}):
            response = client.post(
                "/api/consent",
                json={"consent_version": "1.0"},
            )
        assert response.status_code == 503

    def test_consent_grants_and_transitions(self, client, mock_profile_repo):
        """Granting consent transitions PENDING to ONBOARDING."""
        mock_profile_repo.get_by_user_id.return_value = {
            "id": TEST_PROFILE_ID,
            "user_id": TEST_USER_ID,
            "phase": "PENDING",
            "consent_given_at": None,
            "consent_revoked_at": None,
        }

        with patch("src.main.get_repos", return_value={"profile": mock_profile_repo}):
            response = client.post(
                "/api/consent",
                json={"consent_version": "1.0"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "consent_granted"
        assert data["phase"] == "ONBOARDING"


class TestProfile:
    """Tests for /api/profile endpoint."""

    def test_profile_returns_data(self, client, mock_profile_repo):
        with patch("src.main.get_repos", return_value={"profile": mock_profile_repo}):
            response = client.get("/api/profile")

        assert response.status_code == 200
        data = response.json()
        assert data["display_name"] == "Test Patient"
        assert data["phase"] == "ONBOARDING"
        assert data["consent_given"] is True

    def test_profile_returns_503_without_repo(self, client):
        with patch("src.main.get_repos", return_value={}):
            response = client.get("/api/profile")
        assert response.status_code == 503

    def test_profile_returns_404_when_not_found(self, client):
        mock_repo = MagicMock()
        mock_repo.get_by_user_id.return_value = None

        with patch("src.main.get_repos", return_value={"profile": mock_repo}):
            response = client.get("/api/profile")
        assert response.status_code == 404


class TestGoals:
    """Tests for /api/goals endpoint."""

    def test_goals_returns_list(self, client, mock_goal_repo):
        with patch("src.main.get_repos", return_value={"goal": mock_goal_repo}):
            response = client.get("/api/goals")

        assert response.status_code == 200
        data = response.json()
        assert len(data["goals"]) == 1

    def test_goals_returns_503_without_repo(self, client):
        with patch("src.main.get_repos", return_value={}):
            response = client.get("/api/goals")
        assert response.status_code == 503


class TestConversation:
    """Tests for /api/conversation endpoint."""

    def test_conversation_returns_turns(self, client, mock_conversation_repo):
        with patch("src.main.get_repos", return_value={"conversation": mock_conversation_repo}):
            response = client.get("/api/conversation")

        assert response.status_code == 200
        data = response.json()
        assert len(data["turns"]) == 2
        assert data["total"] == 2

    def test_conversation_returns_503_without_repo(self, client):
        with patch("src.main.get_repos", return_value={}):
            response = client.get("/api/conversation")
        assert response.status_code == 503


class TestRateLimiting:
    """Tests for rate limiting."""

    def test_rate_limit_allows_normal_usage(self):
        """Under-limit requests pass."""
        # Should not raise for the first 10 calls
        for _ in range(10):
            check_rate_limit("test-user", max_per_minute=10)

    def test_rate_limit_blocks_excess(self):
        """Over-limit requests are blocked."""
        from fastapi import HTTPException

        for _ in range(10):
            check_rate_limit("test-user-2", max_per_minute=10)

        with pytest.raises(HTTPException) as exc_info:
            check_rate_limit("test-user-2", max_per_minute=10)

        assert exc_info.value.status_code == 429


# --- Admin endpoint tests ---


class TestAdminEndpoints:
    """Tests for /api/admin/* endpoints."""

    def test_admin_patients_returns_list(self):
        """GET /api/admin/patients returns patient list."""
        import sqlite3

        from src.db.schema import init_db
        from src.db.seed import seed_db

        db = sqlite3.connect(":memory:", check_same_thread=False)
        db.row_factory = sqlite3.Row
        init_db(db)
        seed_db(db)

        with patch("src.db.client.get_db", return_value=db), patch(
            "src.main.get_settings",
            return_value=MagicMock(database_path=":memory:"),
        ):
            client = TestClient(app)
            resp = client.get("/api/admin/patients")

        assert resp.status_code == 200
        data = resp.json()
        assert "patients" in data
        assert len(data["patients"]) == 3

        # Check patient fields
        patient = data["patients"][0]
        assert "display_name" in patient
        assert "phase" in patient
        assert "active_goals_count" in patient
        assert "adherence_pct" in patient
        assert "alerts_count" in patient

    def test_admin_alerts_returns_list(self):
        """GET /api/admin/alerts returns alert list."""
        import sqlite3

        from src.db.schema import init_db
        from src.db.seed import seed_db

        db = sqlite3.connect(":memory:", check_same_thread=False)
        db.row_factory = sqlite3.Row
        init_db(db)
        seed_db(db)

        with patch("src.db.client.get_db", return_value=db), patch(
            "src.main.get_settings",
            return_value=MagicMock(database_path=":memory:"),
        ):
            client = TestClient(app)
            resp = client.get("/api/admin/alerts")

        assert resp.status_code == 200
        data = resp.json()
        assert "alerts" in data
        assert len(data["alerts"]) >= 1

        alert = data["alerts"][0]
        assert "patient_name" in alert
        assert "urgency" in alert
        assert "message" in alert

    def test_admin_reset_reseeds(self):
        """POST /api/admin/reset re-seeds database."""
        import sqlite3

        from src.db.schema import init_db
        from src.db.seed import seed_db

        db = sqlite3.connect(":memory:", check_same_thread=False)
        db.row_factory = sqlite3.Row
        init_db(db)
        seed_db(db)

        with patch("src.db.client.get_db", return_value=db), patch(
            "src.main.get_settings",
            return_value=MagicMock(database_path=":memory:"),
        ):
            client = TestClient(app)
            resp = client.post("/api/admin/reset")

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "reset_complete"
        assert data["patients_count"] == 3
