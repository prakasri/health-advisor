from pathlib import Path

from pydantic import field_validator
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
    # Only for API keys not scoped to a workspace (sent as the anthropic-workspace-id header).
    anthropic_workspace_id: str | None = None
    llm_model: str = "claude-sonnet-5"
    llm_effort_writer: str = "low"
    llm_effort_judge: str = "medium"
    llm_max_tokens: int = 16000
    llm_timeout_s: float = 60.0
    tracing_enabled: bool = True
    phoenix_collector_endpoint: str = "http://localhost:6006/v1/traces"
    phoenix_project: str = "health-advisor"
    # Hosted Phoenix (Arize Phoenix Cloud) needs an API key; local Phoenix does not.
    phoenix_api_key: str | None = None
    specs_dir: Path = REPO_ROOT / "specs"
    share_link_days: int = 30
    retention_days: int = 90

    @field_validator("database_url")
    @classmethod
    def _psycopg_driver(cls, v: str) -> str:
        # Hosted Postgres (Neon) hands out postgresql:// URLs; SQLAlchemy needs the psycopg driver.
        for prefix in ("postgresql://", "postgres://"):
            if v.startswith(prefix):
                return "postgresql+psycopg://" + v[len(prefix) :]
        return v


settings = Settings()
