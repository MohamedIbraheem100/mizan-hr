"""Engine + session factory. One place decides how we connect.

- DATABASE_URL from settings: Neon in prod, docker compose locally, SQLite in tests.
- `postgresql://` is rewritten to `postgresql+psycopg://` so SQLAlchemy uses psycopg 3
  (its default would look for the old psycopg2 driver).
- Small pool with pre-ping: Neon scales to zero and drops idle connections; pre-ping
  detects a dead connection before we use it instead of failing the request.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from mizan.core.config import get_settings


def normalize_url(url: str) -> str:
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    if url.startswith("postgres://"):  # some dashboards still hand out this form
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    return url


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set (see .env.example)")
    url = normalize_url(url)
    if url.startswith("sqlite"):
        # In-memory SQLite lives per connection; StaticPool keeps ONE connection so
        # every session (and every test) sees the same tables.
        return create_engine(url, connect_args={"check_same_thread": False}, poolclass=StaticPool)
    return create_engine(url, pool_pre_ping=True, pool_size=2, max_overflow=3)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI dependency: one session per request, always closed."""
    with get_sessionmaker()() as session:
        yield session
