"""Shared test doubles. No test in this suite needs network or API keys."""

import json

import pytest
from pydantic import BaseModel

from mizan.llm.providers.base import ProviderError

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
    a raw string, or an Exception instance (raised)."""

    def __init__(self, name: str, replies: list) -> None:
        self.name = name
        self._replies = list(replies)
        self.calls: list[dict] = []

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        self.calls.append({"system": system, "user": user, "schema": schema.__name__})
        if not self._replies:
            raise AssertionError(f"{self.name}: no scripted reply left")
        reply = self._replies.pop(0)
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
