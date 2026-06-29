import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _default_database_url() -> str:
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
    finetuned_model_id: str = "your-username/code-review-mistral-lora"
    inference_mode: str = "demo"  # demo | local | huggingface
    hf_inference_api_url: str = "https://api-inference.huggingface.co/models"
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"
    database_url: str = ""
    admin_api_key: str = "change-me-in-production"
    storage_enabled: bool = True

    @property
    def cors_origin_list(self) -> list[str]:
        origins = [o.strip() for o in self.cors_origins.split(",") if o.strip()]
        vercel_url = os.environ.get("VERCEL_URL")
        if vercel_url:
            origins.append(f"https://{vercel_url}")
        return origins


settings = Settings()
if not settings.database_url:
    settings.database_url = _default_database_url()
