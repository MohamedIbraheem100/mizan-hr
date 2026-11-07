import json

import pytest

from mizan.core.config import Settings
from mizan.llm.gateway import LLMGateway, LLMUnavailableError, provider_chain
from mizan.llm.providers.base import ProviderError, parse_retry_after
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


def test_rate_limited_provider_is_skipped_until_its_cooldown_ends(valid_rubric):
    a = FakeProvider("groq-a", [ProviderError("429", retry_after_s=30), valid_rubric])
    b = FakeProvider("groq-b", [valid_rubric, valid_rubric])
    gw = LLMGateway([a, b], max_retry_wait_s=15)
    assert _ask(gw).provider == "groq-b"  # a said 429 -> b answered
    assert _ask(gw).provider == "groq-b"  # a is cooling: not even called
    assert len(a.calls) == 1 and len(b.calls) == 2


def test_short_cooldown_is_waited_out_when_nobody_else_is_available(valid_rubric):
    p = FakeProvider("groq", [ProviderError("429", retry_after_s=0.01), valid_rubric])
    gw = LLMGateway([p], max_retry_wait_s=5)
    with pytest.raises(LLMUnavailableError):
        _ask(gw)  # first call: 429, no fallback
    res = _ask(gw)  # second call: waits the 10 ms cooldown, then succeeds
    assert res.provider == "groq" and len(p.calls) == 2


def test_long_cooldown_with_no_alternative_fails_fast(valid_rubric):
    p = FakeProvider("groq", [ProviderError("429", retry_after_s=90)])
    gw = LLMGateway([p], max_retry_wait_s=15)
    with pytest.raises(LLMUnavailableError):
        _ask(gw)
    with pytest.raises(LLMUnavailableError, match="cooling down"):
        _ask(gw)
    assert len(p.calls) == 1


def test_all_providers_down_raises(down_provider):
    also_down = FakeProvider("groq", [ProviderError("groq: 401 invalid key")])
    with pytest.raises(LLMUnavailableError, match="groq: 401"):
        _ask(LLMGateway([down_provider, also_down]))


def test_gateway_requires_a_provider():
    with pytest.raises(ValueError):
        LLMGateway([])


# ---------- config parsing ----------
def test_parse_retry_after_formats():
    assert parse_retry_after("Please try again in 10.185s. Need more") == pytest.approx(10.185)
    assert parse_retry_after("try again in 554.9ms") == pytest.approx(0.5549)
    assert parse_retry_after("Please retry in 23.4s.") == pytest.approx(23.4)
    assert parse_retry_after("'retryDelay': '7s'") == pytest.approx(7.0)
    assert parse_retry_after("Invalid API Key") is None


def test_provider_chain_prefers_llm_providers_and_dedupes():
    chain = "groq:openai/gpt-oss-120b, groq:openai/gpt-oss-20b,gemini,groq:openai/gpt-oss-20b"
    s = Settings(llm_providers=chain)
    assert provider_chain(s) == [
        ("groq", "openai/gpt-oss-120b"),
        ("groq", "openai/gpt-oss-20b"),
        ("gemini", None),
    ]


def test_provider_chain_falls_back_to_legacy_pair():
    s = Settings(llm_providers="", llm_provider="groq", llm_fallback_provider="none")
    assert provider_chain(s) == [("groq", None)]
