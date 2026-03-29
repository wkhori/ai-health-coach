"""Demo readiness tests — verify seed data, patient journeys, and endpoint availability.

5 tests required to confirm the system is demo-ready.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from src.graph.nodes.phase_router import route_by_phase
from src.main import app, get_current_user

TEST_USER_ID = "00000000-0000-0000-0000-000000000001"


async def mock_get_current_user():
    return {"user_id": TEST_USER_ID}


app.dependency_overrides[get_current_user] = mock_get_current_user


def _make_state(**overrides) -> dict:
    """Create a minimal HealthCoachState dict for testing."""
    defaults = {
        "messages": [],
        "user_id": TEST_USER_ID,
        "profile_id": str(uuid4()),
        "phase": "PENDING",
        "consent_given": False,
        "conversation_summary": "",
        "turn_count": 0,
        "active_goals": [],
        "adherence_summary": {},
        "safety_result": {},
        "is_scheduled_message": False,
        "scheduled_message_type": "",
        "response_text": "",
    }
    defaults.update(overrides)
    return defaults


class TestDemoSeedData:
    """Verify seed data module is importable and contains expected patients."""

    def test_seed_data_exists_and_importable(self):
        """Seed module can be imported and get_seed_data returns data."""
        from src.db.seed import get_seed_data

        data = get_seed_data()
        assert isinstance(data, dict)
        assert "profiles" in data
        assert "goals" in data
        assert "milestones" in data
        assert "conversation_turns" in data
        assert "safety_audit_log" in data
        assert "clinician_alerts" in data
        assert "reminders" in data
        assert "conversation_summaries" in data

    def test_seed_data_has_three_patients(self):
        """Seed data contains exactly 3 patient profiles."""
        from src.db.seed import get_seed_data

        data = get_seed_data()
        profiles = data["profiles"]
        assert len(profiles) == 3

        names = {p["display_name"] for p in profiles}
        assert names == {"Sarah", "Marcus", "Elena"}


class TestDemoPatientJourneys:
    """Verify each demo patient routes correctly based on their phase."""

    def test_sarah_active_routes_to_active_subgraph(self):
        """Sarah (ACTIVE) routes to the active subgraph."""
        state = _make_state(phase="ACTIVE", consent_given=True)
        route = route_by_phase(state)
        assert route == "active_subgraph"

    def test_marcus_onboarding_routes_to_onboarding_subgraph(self):
        """Marcus (ONBOARDING) routes to the onboarding subgraph."""
        state = _make_state(phase="ONBOARDING", consent_given=True)
        route = route_by_phase(state)
        assert route == "onboarding_subgraph"

    def test_elena_re_engaging_routes_to_re_engaging_subgraph(self):
        """Elena (RE_ENGAGING) routes to the re-engaging subgraph."""
        state = _make_state(phase="RE_ENGAGING", consent_given=True)
        route = route_by_phase(state)
        assert route == "re_engaging_subgraph"


class TestDemoEndpoints:
    """Verify all API endpoints respond without 500 errors."""

    def test_all_endpoints_respond(self):
        """Hit all GET endpoints with mock auth; verify no 500s."""
        client = TestClient(app, raise_server_exceptions=False)

        # Health check (no auth needed)
        response = client.get("/api/health")
        assert response.status_code == 200

        # Profile — will return 503 without repos, which is expected (not 500)
        with patch("src.main.get_repos", return_value={}):
            response = client.get("/api/profile")
            assert response.status_code in (200, 404, 503)
            assert response.status_code != 500

        # Goals — will return 503 without repos
        with patch("src.main.get_repos", return_value={}):
            response = client.get("/api/goals")
            assert response.status_code in (200, 503)
            assert response.status_code != 500

        # Conversation — will return 503 without repos
        with patch("src.main.get_repos", return_value={}):
            response = client.get("/api/conversation")
            assert response.status_code in (200, 503)
            assert response.status_code != 500

        # Consent POST — will return 503 without repos
        with patch("src.main.get_repos", return_value={}):
            response = client.post(
                "/api/consent",
                json={"consent_version": "1.0"},
            )
            assert response.status_code in (200, 503)
            assert response.status_code != 500

        # Chat sync — with mocked graph
        mock_graph = AsyncMock()
        mock_graph.ainvoke.return_value = {
            "response_text": "Hello!",
            "phase": "ONBOARDING",
            "safety_result": {"classification": "safe", "action": "passed"},
        }
        with patch("src.main.get_graph", return_value=mock_graph):
            response = client.post(
                "/api/chat/sync",
                json={"message": "hello"},
            )
            assert response.status_code == 200
            assert response.status_code != 500
