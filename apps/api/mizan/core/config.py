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

    # LLM gateway. Preferred: a comma-separated chain, each item "name" or "name:model",
    # e.g. "groq:openai/gpt-oss-120b,groq:openai/gpt-oss-20b,gemini". Groq rate-limits
    # per model, so listing several models multiplies free-tier throughput.
    llm_providers: str = ""
    # Legacy pair, used only when llm_providers is empty.
    llm_provider: str = "gemini"
    llm_fallback_provider: str = "groq"  # "none" disables the fallback
    llm_timeout_s: float = 60.0
    llm_max_retry_wait_s: float = 15.0  # honour "retry in N s" up to this; beyond it, fall back
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.5-flash"
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    # gpt-oss models "think" before answering; low effort = fewer tokens, faster, same JSON.
    groq_reasoning_effort: str = "low"
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
