from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_path: str = "health_coach.db"

    # Anthropic (optional for demo without LLM)
    anthropic_api_key: str = ""

    # LangSmith (optional)
    langchain_tracing_v2: bool = False
    langchain_api_key: str = ""
    langchain_project: str = "ai-health-coach"

    # Configurable constants
    summarize_every_n_turns: int = 6
    re_engage_schedule: str = "2,5,7"
    max_re_engage_attempts: int = 3
    inactivity_threshold_hours: int = 48
    rate_limit_per_minute: int = 10
    sse_keepalive_seconds: int = 15
    log_level: str = "INFO"
    cors_origins: str = "http://localhost:3000"

    # Model config
    llm_model: str = "claude-haiku-4-5-20251001"
    llm_temperature: float = 0.7
    llm_max_tokens: int = 1024
    safety_temperature: float = 0.0
    safety_max_tokens: int = 256

    # Webhook auth
    webhook_secret: str = "demo-secret"

    @property
    def re_engage_days(self) -> list[int]:
        return [int(d.strip()) for d in self.re_engage_schedule.split(",")]

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
