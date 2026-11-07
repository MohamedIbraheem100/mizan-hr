"""Shapes that flow through the screening pipeline and out of POST /screen.

Two families:
- *Draft models: what we ask the LLM to produce (never trusted as-is).
- Final models: what CODE builds after verification and scoring.
"""

from typing import Literal

from pydantic import BaseModel, Field

Verdict = Literal["met", "partial", "not_met", "no_evidence"]

VERDICT_VALUE: dict[str, float] = {"met": 1.0, "partial": 0.5, "not_met": 0.0, "no_evidence": 0.0}


# ---------- Redact (Blind mode) ----------
class RedactDraft(BaseModel):
    """PII strings the model spotted. Code does the actual replacement."""

    person_names: list[str] = Field(default_factory=list)
    other_identifiers: list[str] = Field(
        default_factory=list,
        description="nationality, religion, marital status, gender words, photo captions",
    )


# ---------- Extract ----------
class Experience(BaseModel):
    title: str = ""
    organization: str = ""
    period: str = Field(default="", description="as written, e.g. 2021-2025")
    years: float | None = Field(default=None, ge=0, le=50)
    line_ids: list[str] = Field(default_factory=list)


class CandidateProfile(BaseModel):
    headline: str = ""
    total_years_experience: float | None = Field(default=None, ge=0, le=60)
    skills: list[str] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    education: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)


# ---------- Judge ----------
class Evidence(BaseModel):
    line_id: str
    quote: str = Field(min_length=1, max_length=400)


class JudgmentDraft(BaseModel):
    criterion_id: str
    verdict: Verdict
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning: str = Field(default="", max_length=400)


class JudgeDraft(BaseModel):
    judgments: list[JudgmentDraft]


class CriterionJudgment(BaseModel):
    """A judgment after Verify: every quote left here exists in the cited line."""

    criterion_id: str
    criterion_name: str
    criterion_type: Literal["must_have", "nice_to_have"]
    weight: float
    verdict: Verdict
    evidence: list[Evidence] = Field(default_factory=list)
    dropped_evidence: list[Evidence] = Field(
        default_factory=list, description="quotes the model cited that were NOT in the CV"
    )
    reasoning: str = ""
    verdict_before_verify: Verdict | None = Field(
        default=None, description="set when Verify downgraded the verdict"
    )


# ---------- Explain ----------
class Explanation(BaseModel):
    strengths: list[str] = Field(default_factory=list, max_length=5)
    gaps: list[str] = Field(default_factory=list, max_length=5)
    summary: str = Field(default="", max_length=400)
    interview_questions: list[str] = Field(
        default_factory=list,
        max_length=3,
        description="gaps or date gaps phrased as questions, never as penalties",
    )


# ---------- Final result ----------
class ScoreBreakdown(BaseModel):
    score: int = Field(ge=0, le=100)
    weighted_sum: float
    weight_total: float
    must_haves_met: bool
    missing_must_haves: list[str] = Field(default_factory=list)


class VerifyStats(BaseModel):
    quotes_checked: int = 0
    quotes_verified: int = 0
    quotes_dropped: int = 0
    verdicts_downgraded: int = 0


class ScreeningResult(BaseModel):
    candidate_ref: str
    language: Literal["ar", "en"]
    blind: bool
    score: int
    must_haves_met: bool
    missing_must_haves: list[str]
    judgments: list[CriterionJudgment]
    strengths: list[str]
    gaps: list[str]
    summary: str
    interview_questions: list[str]
    profile: CandidateProfile
    verify: VerifyStats
    line_count: int
    llm_calls: int
    duration_ms: int


# ---------- Progress events (SSE) ----------
NodeName = Literal["parse", "redact", "extract", "judge", "verify", "score", "explain"]


class ProgressEvent(BaseModel):
    node: NodeName
    status: Literal["running", "done", "skipped", "error"]
    detail: dict = Field(default_factory=dict)
