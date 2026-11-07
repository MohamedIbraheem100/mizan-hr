"""Application settings, read from environment variables (12-factor).

Locally the values come from `.env`; in production from Vercel env vars.
Never hard-code a key here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# apps/api/mizan/core/config.py -> repo root is 4 levels up. Looking there (and in
# apps/api) means `uvicorn`/`pytest` find .env no matter which folder you run from.
# Real env vars (docker compose, Vercel) always win over the file.
_REPO_ROOT = Path(__file__).resolve().parents[4]
_ENV_FILES = (_REPO_ROOT / ".env", _REPO_ROOT / "apps" / "api" / ".env")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES, env_file_encoding="utf-8", extra="ignore"
    )

    app_env: str = "development"
    log_level: str = "INFO"

    # LLM gateway: provider order is [llm_provider, llm_fallback_provider]
    llm_provider: str = "gemini"
    llm_fallback_provider: str = "groq"  # "none" disables the fallback
    llm_timeout_s: float = 60.0
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    openai_api_key: str = ""

    # Storage (used from M4)
    database_url: str = ""
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""

    # Limits
    max_jd_chars: int = 10_000


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is parsed once per process."""
    return Settings()
