import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _normalize_db_url(url: str) -> str:
    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)
    if url.startswith("postgresql://") and "+asyncpg" not in url and "+psycopg" not in url:
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


def _default_database_url() -> str:
    for key in ("DATABASE_URL", "POSTGRES_URL", "POSTGRES_PRISMA_URL"):
        if os.environ.get(key):
            return _normalize_db_url(os.environ[key])
    if os.environ.get("VERCEL"):
        return "sqlite+aiosqlite:////tmp/reviews.db"
    return f"sqlite+aiosqlite:///{PROJECT_ROOT / 'data' / 'reviews.db'}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    hf_token: str = ""
    base_model_id: str = "mistralai/Mistral-7B-Instruct-v0.3"
    finetuned_model_id: str = "HimanshuuDua/code-review-mistral-lora"
    codereviewer_model_id: str = "microsoft/codereviewer"
    inference_mode: str = "hybrid"  # demo | hybrid | huggingface | local
    hf_inference_api_url: str = "https://api-inference.huggingface.co/models"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    app_base_url: str = "http://localhost:5173"
    database_url: str = ""
    admin_api_key: str = "change-me-in-production"
    storage_enabled: bool = True
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 30
    github_client_id: str = ""
    github_client_secret: str = ""
    inference_fallback_demo: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        for key in ("VERCEL_URL", "VERCEL_BRANCH_URL"):
            url = os.environ.get(key)
            if url:
                origins.append(f"https://{url}")
        if self.app_base_url.startswith("http"):
            origins.append(self.app_base_url.rstrip("/"))
        return list(dict.fromkeys(origins))


settings = Settings()
if not settings.database_url:
    settings.database_url = _default_database_url()
else:
    settings.database_url = _normalize_db_url(settings.database_url)
