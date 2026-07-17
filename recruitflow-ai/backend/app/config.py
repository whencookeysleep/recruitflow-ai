from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    backend_cors_origins: str = "http://localhost:3000"
    database_url: str = "sqlite:///./data/recruitflow.db"
    resume_inbox_dir: Path = Path("./data/resume_inbox")
    upload_dir: Path = Path("./data/uploads")
    export_dir: Path = Path("./data/exports")
    ai_provider: str = "mock"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    wecom_webhook_url: str | None = None
    cors_origins: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def allowed_origins(self) -> list[str]:
        if self.cors_origins:
            return self.cors_origins
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
