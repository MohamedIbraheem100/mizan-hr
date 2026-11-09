"""Application settings, read from environment variables (12-factor).

Locally the values come from `.env`; in production from Vercel env vars.
Never hard-code a key here.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Look for a .env in this file's ancestors (apps/api/.env, repo-root/.env, ...), so
# `uvicorn`/`pytest` find it no matter which folder you run from. Missing files are
# skipped, and inside Docker (/app/mizan/core/config.py has only 3 ancestors) nothing
# breaks. Real env vars (docker compose, Vercel) always win over any file.
_ENV_FILES = tuple(parent / ".env" for parent in Path(__file__).resolve().parents[:5])


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
    rate_limit_per_day: int = 10  # CVs per visitor per day (public demo)
    rate_limit_global_per_day: int = 200  # CVs per day across all visitors (protects quota)
    # Trusted server-to-server callers (the owner's portfolio "Recruiter Mode") all arrive from
    # shared Vercel egress IPs, so the per-visitor limit would count them as one visitor.
    # A request carrying X-Internal-Key == INTERNAL_KEY skips the visitor limit and is counted
    # on its own daily cap instead. Empty key = feature off.
    internal_key: str = ""
    rate_limit_internal_per_day: int = 100

    # Ops
    cleanup_token: str = ""  # shared secret for POST /admin/cleanup (GitHub Actions cron)
    cors_origins: str = "https://mizan-hr.vercel.app,http://localhost:3000"
    cors_origin_regex: str = r"https://mizan-hr(-[a-z0-9-]+)?-ai-engineer12\.vercel\.app"


@lru_cache
def get_settings() -> Settings:
    """Cached so the .env file is parsed once per process."""
    return Settings()
