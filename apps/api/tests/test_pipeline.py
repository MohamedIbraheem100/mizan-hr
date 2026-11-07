"""End-to-end pipeline with scripted LLM replies: event order, blind mode, injection."""

from mizan.llm.gateway import LLMGateway
from mizan.pipeline.graph import run_screening
from mizan.pipeline.parse import parse_text
from mizan.schemas.rubric import Rubric
from mizan.schemas.screening import ProgressEvent, ScreeningResult
from tests.conftest import FakeProvider
from tests.pipeline_fixtures import (
    CV_LINES_EN,
    EXPLAIN_REPLY,
    INJECTION_LINE,
    JUDGE_REPLY_FOOLED,
    JUDGE_REPLY_HONEST,
    PROFILE_REPLY,
    REDACT_REPLY,
    RUBRIC,
)


def replies(*, judge=JUDGE_REPLY_HONEST, blind=False) -> dict[str, list]:
    """Replies keyed by schema: extract and judge run in parallel, so order varies."""
    r = {
        "CandidateProfile": [PROFILE_REPLY],
        "JudgeDraft": [judge],
        "Explanation": [EXPLAIN_REPLY],
    }
    if blind:
        r["RedactDraft"] = [REDACT_REPLY]
    return r


def _run(scripted, *, lines=CV_LINES_EN, blind=False):
    provider = FakeProvider("fake", scripted)
    items = list(
        run_screening(
            LLMGateway([provider]),
            rubric=Rubric.model_validate(RUBRIC),
            cv=parse_text("\n".join(lines)),
            blind=blind,
            candidate_ref="Candidate #1",
        )
    )
    events = [i for i in items if isinstance(i, ProgressEvent)]
    result = next(i for i in items if isinstance(i, ScreeningResult))
    return events, result, provider


def test_events_follow_stage_order_and_result_is_last():
    events, result, provider = _run(replies())
    seq = [(e.node, e.status) for e in events]
    # Stage 1: redact. Stage 2: extract + judge announced together, finish in any order.
    assert seq[:4] == [
        ("redact", "running"),
        ("redact", "skipped"),
        ("extract", "running"),
        ("judge", "running"),
    ]
    assert sorted(seq[4:6]) == [("extract", "done"), ("judge", "done")]
    assert seq[6:] == [
        ("verify", "running"),
        ("verify", "done"),
        ("score", "running"),
        ("score", "done"),
        ("explain", "running"),
        ("explain", "done"),
    ]
    assert result.score == 100 and result.must_haves_met is True
    assert result.llm_calls == 3 and len(provider.calls) == 3
    assert result.verify.quotes_verified == 3 and result.verify.quotes_dropped == 0
    assert result.summary.startswith("Strong backend profile")


def test_blind_mode_redacts_before_any_judgement():
    events, result, provider = _run(replies(blind=True), blind=True)
    assert ("redact", "done") in [(e.node, e.status) for e in events]
    assert result.llm_calls == 4 and result.blind is True
    # Extract and Judge must never see the name/PII; professional content survives.
    for call in provider.calls:
        if call["schema"] in ("CandidateProfile", "JudgeDraft"):
            assert "Ahmed" not in call["user"] and "example.com" not in call["user"]
            assert "Married" not in call["user"] and "Egyptian" not in call["user"]
            assert "FastAPI" in call["user"]


def test_injection_cv_cannot_buy_a_high_score():
    """CLAUDE.md: the injection test CV must stay in the suite and must not score high.

    Even if the model is fooled (met everywhere, quotes invented), Verify drops every
    fabricated quote, the verdicts fall to no_evidence, and the score is 0 with every
    must-have flagged.
    """
    lines = CV_LINES_EN[:3] + [INJECTION_LINE]  # a thin CV plus the attack line
    _, result, _ = _run(replies(judge=JUDGE_REPLY_FOOLED), lines=lines)
    assert result.score == 0
    assert result.must_haves_met is False
    assert sorted(result.missing_must_haves) == ["PostgreSQL", "Python 3+ years"]
    assert result.verify.quotes_dropped == 3 and result.verify.verdicts_downgraded == 3
    assert all(
        j.verdict == "no_evidence" and j.verdict_before_verify == "met" for j in result.judgments
    )
