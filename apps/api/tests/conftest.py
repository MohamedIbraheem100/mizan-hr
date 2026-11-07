"""Shared test doubles. No test in this suite needs network or API keys.

Database: tests run on in-memory SQLite unless DATABASE_URL is already set in the
environment (CI sets it to a real Postgres service). Real env vars beat .env, so a
developer's Neon URL in .env is never touched by the test suite.
"""

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")  # before any settings load

import json  # noqa: E402

import pytest  # noqa: E402
from pydantic import BaseModel  # noqa: E402

from mizan.db.models import Base  # noqa: E402
from mizan.db.session import get_engine  # noqa: E402
from mizan.llm.providers.base import ProviderError  # noqa: E402


@pytest.fixture(autouse=True)
def fresh_tables():
    """Every test starts with empty tables and leaves none behind."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


VALID_RUBRIC = {
    "job_title": "Sales Manager",
    "language": "en",
    "criteria": [
        {"name": "B2B sales experience", "type": "must_have", "weight": 0.5, "min_years": 3},
        {"name": "Arabic and English", "type": "must_have", "weight": 0.3},
        {"name": "CRM tools", "type": "nice_to_have", "weight": 0.2},
    ],
}


class FakeProvider:
    """Replays scripted replies. A reply can be a dict (serialized to JSON),
    a raw string, or an Exception instance (raised).

    `replies` is either a list (consumed in call order) or a dict keyed by schema
    name (each key its own queue). The dict form is needed when graph nodes run
    in parallel and call order is not deterministic.
    """

    def __init__(self, name: str, replies: list | dict[str, list]) -> None:
        self.name = name
        self._by_schema = (
            {k: list(v) for k, v in replies.items()} if isinstance(replies, dict) else None
        )
        self._replies = list(replies) if isinstance(replies, list) else []
        self.calls: list[dict] = []

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        self.calls.append({"system": system, "user": user, "schema": schema.__name__})
        queue = (
            self._by_schema.get(schema.__name__) if self._by_schema is not None else self._replies
        )
        if not queue:
            raise AssertionError(f"{self.name}: no scripted reply left for {schema.__name__}")
        reply = queue.pop(0)
        if isinstance(reply, Exception):
            raise reply
        if isinstance(reply, dict):
            return json.dumps(reply)
        return reply


@pytest.fixture
def valid_rubric() -> dict:
    return json.loads(json.dumps(VALID_RUBRIC))


@pytest.fixture
def down_provider() -> FakeProvider:
    return FakeProvider("down", [ProviderError("down: 503"), ProviderError("down: 503")])
