"""Comprehensive tests for the auth system and auth-related API endpoints."""

import sqlite3
from unittest.mock import patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.db.schema import init_db
from src.main import (
    _hash_password,
    _verify_password,
    app,
    get_current_user,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_test_db() -> sqlite3.Connection:
    """Create a fresh in-memory SQLite database with the full schema."""
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    init_db(conn)
    return conn


def _register_user(conn: sqlite3.Connection, email: str = "alice@example.com",
                   password: str = "secret123", name: str = "Alice") -> dict:
    """Insert a user + profile + session directly into the DB and return metadata."""
    user_id = str(uuid4())
    password_hash = _hash_password(password)
    token = str(uuid4())
    profile_id = str(uuid4())
    display_name = name or email.split("@")[0]

    conn.execute(
        "INSERT INTO users (id, email, password_hash) VALUES (?, ?, ?)",
        (user_id, email, password_hash),
    )
    conn.execute(
        "INSERT INTO sessions (token, user_id) VALUES (?, ?)",
        (token, user_id),
    )
    conn.execute(
        "INSERT INTO profiles (id, user_id, display_name, phase) VALUES (?, ?, ?, ?)",
        (profile_id, user_id, display_name, "PENDING"),
    )
    conn.commit()
    return {
        "user_id": user_id,
        "email": email,
        "token": token,
        "profile_id": profile_id,
        "display_name": display_name,
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def test_db():
    """Yield a fresh in-memory DB. Closes automatically after the test."""
    conn = _make_test_db()
    yield conn
    conn.close()


@pytest.fixture()
def auth_client(test_db):
    """TestClient that patches get_db and get_settings so auth endpoints use the
    in-memory test database. The dependency override for get_current_user is
    *removed* so that we exercise real auth logic.
    """
    # Remove the global override from test_api.py if it leaked
    overrides_backup = dict(app.dependency_overrides)
    app.dependency_overrides.pop(get_current_user, None)

    with (
        patch("src.db.client.get_db", return_value=test_db),
        patch("src.main.get_settings", return_value=_fake_settings()),
    ):
        yield TestClient(app, raise_server_exceptions=False)

    # Restore original overrides so other test modules are unaffected
    app.dependency_overrides = overrides_backup


def _fake_settings():
    """Return a minimal Settings-like object whose database_path is irrelevant
    because we also patch get_db.
    """
    from src.config import Settings

    return Settings(database_path=":memory:")  # type: ignore[call-arg]


# =========================================================================
# Password hashing
# =========================================================================


class TestPasswordHashing:
    """Unit tests for _hash_password / _verify_password."""

    def test_hash_produces_salt_and_hash(self):
        hashed = _hash_password("password")
        parts = hashed.split(":")
        assert len(parts) == 2
        assert len(parts[0]) > 0  # salt hex
        assert len(parts[1]) > 0  # hash hex

    def test_verify_correct_password(self):
        hashed = _hash_password("mysecret")
        assert _verify_password("mysecret", hashed) is True

    def test_verify_wrong_password(self):
        hashed = _hash_password("mysecret")
        assert _verify_password("wrongpassword", hashed) is False

    def test_different_passwords_different_hashes(self):
        h1 = _hash_password("password1")
        h2 = _hash_password("password2")
        assert h1 != h2

    def test_hash_format_is_hex_colon_hex(self):
        hashed = _hash_password("abc")
        salt_hex, hash_hex = hashed.split(":")
        # Both parts must be valid hex strings
        int(salt_hex, 16)
        int(hash_hex, 16)

    def test_same_password_produces_different_salts(self):
        """Each call generates a random salt, so hashes should differ."""
        h1 = _hash_password("samepassword")
        h2 = _hash_password("samepassword")
        assert h1 != h2

    def test_empty_password_can_be_hashed_and_verified(self):
        hashed = _hash_password("")
        assert _verify_password("", hashed) is True
        assert _verify_password("notempty", hashed) is False

    def test_salt_is_16_bytes_32_hex_chars(self):
        hashed = _hash_password("test")
        salt_hex = hashed.split(":")[0]
        assert len(salt_hex) == 32  # 16 bytes -> 32 hex chars


# =========================================================================
# POST /api/auth/register
# =========================================================================


class TestAuthRegister:
    """Tests for the registration endpoint."""

    def test_register_success(self, auth_client):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "new@example.com", "password": "pass123"},
        )
        assert resp.status_code == 200

    def test_register_returns_token(self, auth_client):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "tok@example.com", "password": "pass123"},
        )
        data = resp.json()
        assert "token" in data
        assert len(data["token"]) > 0

    def test_register_returns_user_info(self, auth_client):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "info@example.com", "password": "pass123"},
        )
        user = resp.json()["user"]
        assert "user_id" in user
        assert user["email"] == "info@example.com"

    def test_register_creates_profile_in_pending_phase(self, auth_client, test_db):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "phase@example.com", "password": "pass123"},
        )
        user_id = resp.json()["user"]["user_id"]
        row = test_db.execute(
            "SELECT phase FROM profiles WHERE user_id = ?", (user_id,)
        ).fetchone()
        assert row is not None
        assert row[0] == "PENDING"

    def test_register_duplicate_email_returns_409(self, auth_client):
        auth_client.post(
            "/api/auth/register",
            json={"email": "dup@example.com", "password": "pass123"},
        )
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "dup@example.com", "password": "other456"},
        )
        assert resp.status_code == 409

    def test_register_with_name(self, auth_client):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "named@example.com", "password": "pass123", "name": "Bob Jones"},
        )
        user = resp.json()["user"]
        assert user["name"] == "Bob Jones"

    def test_register_without_name_uses_email_prefix(self, auth_client):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "prefix@example.com", "password": "pass123"},
        )
        user = resp.json()["user"]
        assert user["name"] == "prefix"

    def test_register_creates_user_in_db(self, auth_client, test_db):
        auth_client.post(
            "/api/auth/register",
            json={"email": "dbcheck@example.com", "password": "pass123"},
        )
        row = test_db.execute(
            "SELECT email FROM users WHERE email = ?", ("dbcheck@example.com",)
        ).fetchone()
        assert row is not None
        assert row[0] == "dbcheck@example.com"

    def test_register_creates_session(self, auth_client, test_db):
        resp = auth_client.post(
            "/api/auth/register",
            json={"email": "sess@example.com", "password": "pass123"},
        )
        token = resp.json()["token"]
        row = test_db.execute(
            "SELECT user_id FROM sessions WHERE token = ?", (token,)
        ).fetchone()
        assert row is not None

    def test_register_password_is_stored_hashed(self, auth_client, test_db):
        auth_client.post(
            "/api/auth/register",
            json={"email": "hashcheck@example.com", "password": "plain123"},
        )
        row = test_db.execute(
            "SELECT password_hash FROM users WHERE email = ?", ("hashcheck@example.com",)
        ).fetchone()
        assert row is not None
        assert ":" in row[0]
        assert row[0] != "plain123"


# =========================================================================
# POST /api/auth/login
# =========================================================================


class TestAuthLogin:
    """Tests for the login endpoint."""

    def test_login_success(self, auth_client, test_db):
        _register_user(test_db, email="login@example.com", password="pass123")
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "login@example.com", "password": "pass123"},
        )
        assert resp.status_code == 200

    def test_login_returns_token(self, auth_client, test_db):
        _register_user(test_db, email="logtok@example.com", password="pass123")
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "logtok@example.com", "password": "pass123"},
        )
        assert "token" in resp.json()
        assert len(resp.json()["token"]) > 0

    def test_login_returns_user_info(self, auth_client, test_db):
        _register_user(test_db, email="loginfo@example.com", password="pass123")
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "loginfo@example.com", "password": "pass123"},
        )
        user = resp.json()["user"]
        assert user["email"] == "loginfo@example.com"
        assert "user_id" in user

    def test_login_wrong_password_returns_401(self, auth_client, test_db):
        _register_user(test_db, email="wrongpw@example.com", password="correct")
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "wrongpw@example.com", "password": "incorrect"},
        )
        assert resp.status_code == 401

    def test_login_nonexistent_email_returns_401(self, auth_client):
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "ghost@example.com", "password": "anything"},
        )
        assert resp.status_code == 401

    def test_login_returns_display_name_from_profile(self, auth_client, test_db):
        _register_user(test_db, email="dispname@example.com", password="pass123", name="Dr. Smith")
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "dispname@example.com", "password": "pass123"},
        )
        user = resp.json()["user"]
        assert user["name"] == "Dr. Smith"

    def test_login_creates_new_session(self, auth_client, test_db):
        info = _register_user(test_db, email="newsess@example.com", password="pass123")
        old_token = info["token"]
        resp = auth_client.post(
            "/api/auth/login",
            json={"email": "newsess@example.com", "password": "pass123"},
        )
        new_token = resp.json()["token"]
        # The login endpoint creates a *new* session token (different from registration token)
        assert new_token != old_token
        # Both tokens should exist in the sessions table
        count = test_db.execute("SELECT COUNT(*) FROM sessions WHERE user_id = ?",
                                (info["user_id"],)).fetchone()[0]
        assert count >= 2

    def test_login_error_message_is_generic(self, auth_client, test_db):
        """Both wrong-password and nonexistent-email return the same detail to prevent
        enumeration attacks."""
        _register_user(test_db, email="enum@example.com", password="pass")
        r1 = auth_client.post("/api/auth/login",
                              json={"email": "enum@example.com", "password": "bad"})
        r2 = auth_client.post("/api/auth/login",
                              json={"email": "nope@example.com", "password": "bad"})
        assert r1.json()["detail"] == r2.json()["detail"] == "Invalid credentials"


# =========================================================================
# POST /api/auth/me
# =========================================================================


class TestAuthMe:
    """Tests for the /api/auth/me endpoint."""

    def test_me_with_valid_token(self, auth_client, test_db):
        info = _register_user(test_db, email="me@example.com", password="pass123", name="MeUser")
        resp = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {info['token']}"},
        )
        assert resp.status_code == 200

    def test_me_without_token_returns_401(self, auth_client):
        resp = auth_client.post("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_invalid_token_returns_401(self, auth_client):
        resp = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": "Bearer totally-invalid-token"},
        )
        assert resp.status_code == 401

    def test_me_returns_user_info(self, auth_client, test_db):
        info = _register_user(test_db, email="meinfo@example.com", password="pass123")
        resp = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {info['token']}"},
        )
        data = resp.json()
        assert data["user_id"] == info["user_id"]
        assert data["email"] == "meinfo@example.com"

    def test_me_returns_display_name(self, auth_client, test_db):
        info = _register_user(test_db, email="medname@example.com", password="pass123",
                              name="Display Name")
        resp = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {info['token']}"},
        )
        assert resp.json()["name"] == "Display Name"

    def test_me_with_empty_bearer_returns_401(self, auth_client):
        resp = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 401


# =========================================================================
# get_current_user dependency (unit-level)
# =========================================================================


class TestGetCurrentUser:
    """Unit tests for the get_current_user dependency function."""

    @pytest.mark.asyncio
    async def test_valid_bearer_token(self, test_db):
        info = _register_user(test_db, email="dep@example.com", password="p")
        request = _fake_request(f"Bearer {info['token']}")

        with (
            patch("src.main.get_settings", return_value=_fake_settings()),
            patch("src.db.client.get_db", return_value=test_db),
        ):
            result = await get_current_user(request)

        assert result["user_id"] == info["user_id"]

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self):
        request = _fake_request("")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_bearer_prefix(self):
        request = _fake_request("Basic abc123")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_empty_token(self):
        request = _fake_request("Bearer ")
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_invalid_token_not_in_sessions(self, test_db):
        request = _fake_request("Bearer not-a-real-token")
        from fastapi import HTTPException

        with (
            patch("src.main.get_settings", return_value=_fake_settings()),
            patch("src.db.client.get_db", return_value=test_db),
        ):
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_dict_with_user_id_key(self, test_db):
        info = _register_user(test_db, email="key@example.com", password="p")
        request = _fake_request(f"Bearer {info['token']}")

        with (
            patch("src.main.get_settings", return_value=_fake_settings()),
            patch("src.db.client.get_db", return_value=test_db),
        ):
            result = await get_current_user(request)

        assert "user_id" in result
        assert isinstance(result["user_id"], str)


# =========================================================================
# End-to-end auth flows
# =========================================================================


class TestAuthEndToEnd:
    """Integration tests exercising register -> login -> authenticated access."""

    def test_register_then_login(self, auth_client):
        # Register
        reg = auth_client.post(
            "/api/auth/register",
            json={"email": "e2e@example.com", "password": "securepass", "name": "E2E User"},
        )
        assert reg.status_code == 200

        # Login with the same credentials
        login = auth_client.post(
            "/api/auth/login",
            json={"email": "e2e@example.com", "password": "securepass"},
        )
        assert login.status_code == 200
        assert login.json()["user"]["email"] == "e2e@example.com"

    def test_register_then_access_me(self, auth_client):
        reg = auth_client.post(
            "/api/auth/register",
            json={"email": "meflow@example.com", "password": "pw", "name": "Me Flow"},
        )
        token = reg.json()["token"]

        me = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "meflow@example.com"
        assert me.json()["name"] == "Me Flow"

    def test_login_then_access_me(self, auth_client, test_db):
        _register_user(test_db, email="loginme@example.com", password="pw", name="Login Me")

        login = auth_client.post(
            "/api/auth/login",
            json={"email": "loginme@example.com", "password": "pw"},
        )
        token = login.json()["token"]

        me = auth_client.post(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == "loginme@example.com"

    def test_register_token_and_login_token_both_work(self, auth_client):
        reg = auth_client.post(
            "/api/auth/register",
            json={"email": "both@example.com", "password": "pw"},
        )
        reg_token = reg.json()["token"]

        login = auth_client.post(
            "/api/auth/login",
            json={"email": "both@example.com", "password": "pw"},
        )
        login_token = login.json()["token"]

        for tok in (reg_token, login_token):
            me = auth_client.post(
                "/api/auth/me",
                headers={"Authorization": f"Bearer {tok}"},
            )
            assert me.status_code == 200

    def test_unauthenticated_cannot_access_me(self, auth_client):
        resp = auth_client.post("/api/auth/me")
        assert resp.status_code == 401


# =========================================================================
# Private helpers
# =========================================================================


class _FakeRequest:
    """Minimal stand-in for a FastAPI Request for unit-testing get_current_user."""

    def __init__(self, auth_header: str):
        self.headers = {"Authorization": auth_header} if auth_header else {}


def _fake_request(auth_header: str) -> _FakeRequest:
    return _FakeRequest(auth_header)
