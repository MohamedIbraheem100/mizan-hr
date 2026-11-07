"""Groq provider behaviour that matters to the gateway, with a stubbed SDK client."""

import httpx
import pytest
from groq import BadRequestError

from mizan.llm.providers.base import ProviderError
from mizan.llm.providers.groq import GroqProvider
from mizan.schemas.rubric import RubricDraft


def _bad_request(body: dict) -> BadRequestError:
    req = httpx.Request("POST", "https://api.groq.com/openai/v1/chat/completions")
    resp = httpx.Response(400, request=req, json=body)
    return BadRequestError("400", response=resp, body=body)


class _StubCompletions:
    def __init__(self, exc: Exception) -> None:
        self._exc = exc

    def create(self, **kwargs):
        raise self._exc


def _provider_raising(exc: Exception) -> GroqProvider:
    p = GroqProvider(api_key="test", model="m")
    p._client.chat.completions = _StubCompletions(exc)  # type: ignore[attr-defined]
    return p


def test_json_validate_failed_is_returned_as_output_not_transport_error():
    exc = _bad_request(
        {
            "error": {
                "code": "json_validate_failed",
                "message": "Failed to generate JSON.",
                "failed_generation": "I'm sorry, but I can't comply with that.",
            }
        }
    )
    out = _provider_raising(exc).generate_json(
        system="s", user="u", schema=RubricDraft, timeout_s=5
    )
    assert out == "I'm sorry, but I can't comply with that."  # gateway will reject + retry


def test_other_bad_requests_are_transport_errors():
    exc = _bad_request({"error": {"code": "model_not_found", "message": "no such model"}})
    with pytest.raises(ProviderError, match="BadRequestError"):
        _provider_raising(exc).generate_json(system="s", user="u", schema=RubricDraft, timeout_s=5)


def test_missing_key_is_a_provider_error():
    with pytest.raises(ProviderError):
        GroqProvider(api_key="", model="m")
