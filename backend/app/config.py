from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """Runtime settings. Locally read from backend/.env; on AWS injected from SSM."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    env: str = "local"
    database_url: str = (
        "postgresql+psycopg://health_advisor:health_advisor@localhost:5432/health_advisor"
    )
    anthropic_api_key: str | None = None
    llm_model: str = "claude-sonnet-5"
    llm_effort_writer: str = "low"
    llm_effort_judge: str = "medium"
    llm_max_tokens: int = 16000
    llm_timeout_s: float = 60.0
    tracing_enabled: bool = True
    phoenix_collector_endpoint: str = "http://localhost:6006/v1/traces"
    phoenix_project: str = "health-advisor"
    specs_dir: Path = REPO_ROOT / "specs"
    share_link_days: int = 30
    retention_days: int = 90


settings = Settings()
