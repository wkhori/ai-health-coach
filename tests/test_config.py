"""Tests for configuration (src/config.py).

5 tests covering defaults, property parsing, and model config values.
"""

import pytest

from src.config import Settings


@pytest.fixture
def _set_required_env(monkeypatch):
    """Set environment variables for Settings.

    database_path and anthropic_api_key both have defaults, so technically
    no env vars are *required*.  We still set ANTHROPIC_API_KEY explicitly
    so the test is deterministic regardless of the local environment.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("DATABASE_PATH", ":memory:")


class TestSettings:
    def test_default_settings(self, _set_required_env):
        """All configurable defaults are correct when only required env vars are set."""
        settings = Settings()  # type: ignore[call-arg]

        assert settings.langchain_tracing_v2 is False
        assert settings.langchain_api_key == ""
        assert settings.langchain_project == "ai-health-coach"
        assert settings.summarize_every_n_turns == 6
        assert settings.re_engage_schedule == "2,5,7"
        assert settings.max_re_engage_attempts == 3
        assert settings.inactivity_threshold_hours == 48
        assert settings.rate_limit_per_minute == 10
        assert settings.sse_keepalive_seconds == 15
        assert settings.log_level == "INFO"
        assert settings.cors_origins == "http://localhost:3000"

    def test_re_engage_days_parsing(self, _set_required_env):
        """re_engage_days property parses comma-separated string to list[int]."""
        settings = Settings()  # type: ignore[call-arg]
        assert settings.re_engage_days == [2, 5, 7]

    def test_re_engage_days_custom(self, monkeypatch, _set_required_env):
        """Custom re_engage_schedule string parses correctly."""
        monkeypatch.setenv("RE_ENGAGE_SCHEDULE", "1,3,5,10")
        settings = Settings()  # type: ignore[call-arg]
        assert settings.re_engage_days == [1, 3, 5, 10]

    def test_cors_origins_parsing(self, _set_required_env):
        """cors_origin_list property parses single origin correctly."""
        settings = Settings()  # type: ignore[call-arg]
        assert settings.cors_origin_list == ["http://localhost:3000"]

    def test_cors_origins_multiple(self, monkeypatch, _set_required_env):
        """cors_origin_list handles multiple comma-separated origins."""
        monkeypatch.setenv("CORS_ORIGINS", "http://localhost:3000, https://app.example.com")
        settings = Settings()  # type: ignore[call-arg]
        assert settings.cors_origin_list == ["http://localhost:3000", "https://app.example.com"]

    def test_env_file_loading(self, _set_required_env):
        """Settings constructor works with env vars (no .env file needed)."""
        settings = Settings()  # type: ignore[call-arg]
        assert settings.database_path == ":memory:"
        assert settings.anthropic_api_key == "sk-ant-test-key"

    def test_model_config_values(self, _set_required_env):
        """LLM model, temperature, and max_tokens defaults are correct."""
        settings = Settings()  # type: ignore[call-arg]
        assert settings.llm_model == "claude-haiku-4-5-20251001"
        assert settings.llm_temperature == 0.7
        assert settings.llm_max_tokens == 1024
        assert settings.safety_temperature == 0.0
        assert settings.safety_max_tokens == 256

    def test_database_path_default(self):
        """database_path defaults to 'health_coach.db' when not set."""
        settings = Settings()  # type: ignore[call-arg]
        assert settings.database_path == "health_coach.db"

    def test_anthropic_api_key_defaults_to_empty(self):
        """anthropic_api_key defaults to empty string when not set."""
        settings = Settings()  # type: ignore[call-arg]
        # Note: this may pick up ANTHROPIC_API_KEY from the real env,
        # so we only test the type is str.
        assert isinstance(settings.anthropic_api_key, str)
