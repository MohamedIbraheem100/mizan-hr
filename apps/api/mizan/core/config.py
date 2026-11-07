"""Application settings, read from environment variables (12-factor).

Locally the values come from `.env`; in production from Vercel env vars.
Never hard-code a key here.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    log_level: str = "INFO"

    # LLM gateway (used from M3)
    llm_provider: str = "gemini"
    llm_fallback_provider: str = "groq"
    gemini_api_key: str = ""
    groq_api_key: str = ""
    openai_api_key: str = ""

    # Storage (used from M4)
    database_url: str = ""
    upstash_redis_rest_url: str = ""
    upstash_redis_rest_token: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is parsed once per process."""
    return Settings()
