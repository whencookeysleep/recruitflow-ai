from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    backend_cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    database_url: str = "sqlite:///./data/recruitflow.db"
    resume_inbox_dir: Path = Path("./data/resume_inbox")
    upload_dir: Path = Path("./data/uploads")
    export_dir: Path = Path("./data/exports")
    ai_provider: str = "mock"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"
    wecom_webhook_url: str | None = None
    tencent_docs_mcp_url: str = "https://docs.qq.com/openapi/mcp"
    tencent_docs_token: str | None = None
    tencent_docs_file_id: str | None = None
    tencent_docs_sheet_id: str | None = None
    public_app_url: str = "http://localhost:3000"
    auth_secret: str = "recruitflow-local-demo-secret"
    auth_token_hours: int = 12
    demo_hr_username: str = "hr_demo"
    demo_hr_password: str = "hr-demo-2026"
    demo_department_username: str = "department_demo"
    demo_department_password: str = "department-demo-2026"
    cors_origins: list[str] = Field(default_factory=list)

    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    def allowed_origins(self) -> list[str]:
        if self.cors_origins:
            return self.cors_origins
        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
