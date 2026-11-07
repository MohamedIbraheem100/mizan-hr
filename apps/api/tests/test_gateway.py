import json

import pytest

from mizan.llm.gateway import LLMGateway, LLMUnavailableError
from mizan.llm.providers.base import ProviderError
from mizan.schemas.rubric import RubricDraft
from tests.conftest import FakeProvider


def _ask(gateway: LLMGateway):
    return gateway.complete_json(system="s", user="u", schema=RubricDraft)


def test_valid_reply_first_try(valid_rubric):
    p = FakeProvider("gemini", [valid_rubric])
    res = _ask(LLMGateway([p]))
    assert res.provider == "gemini"
    assert res.attempts == 1
    assert res.data.job_title == "Sales Manager"


def test_invalid_json_then_retry_succeeds(valid_rubric):
    p = FakeProvider("gemini", ["not json at all", valid_rubric])
    res = _ask(LLMGateway([p]))
    assert res.attempts == 2
    # The retry prompt carries the validation error back to the model.
    assert "previous reply was rejected" in p.calls[1]["user"]


def test_markdown_fences_are_tolerated(valid_rubric):
    p = FakeProvider("gemini", ["```json\n" + json.dumps(valid_rubric) + "\n```"])
    assert _ask(LLMGateway([p])).attempts == 1


def test_two_invalid_replies_fall_back_to_next_provider(valid_rubric):
    bad = FakeProvider("gemini", ["{}", "{}"])
    good = FakeProvider("groq", [valid_rubric])
    res = _ask(LLMGateway([bad, good]))
    assert res.provider == "groq"
    assert res.attempts == 3
    assert len(bad.calls) == 2  # exactly one retry on the first provider


def test_transport_error_skips_retry_and_falls_back(down_provider, valid_rubric):
    good = FakeProvider("groq", [valid_rubric])
    res = _ask(LLMGateway([down_provider, good]))
    assert res.provider == "groq"
    assert len(down_provider.calls) == 1  # no retry on transport failure


def test_all_providers_down_raises(down_provider):
    also_down = FakeProvider("groq", [ProviderError("groq: 401 invalid key")])
    with pytest.raises(LLMUnavailableError, match="groq: 401"):
        _ask(LLMGateway([down_provider, also_down]))


def test_gateway_requires_a_provider():
    with pytest.raises(ValueError):
        LLMGateway([])
