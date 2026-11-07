"""The screening pipeline as a LangGraph graph.

    (parse happens in the route)
        -> redact -> { extract , judge } -> verify -> score -> explain
                      (run in parallel)

Extract and Judge both only need the (redacted) lines, so they run in the same
superstep: one call latency saved per CV. LLM nodes go through the gateway;
verify and score are pure code. The graph is built per gateway so tests can
inject a FakeProvider. `run_screening` streams a ProgressEvent per node and
finally the ScreeningResult.
"""

import json
import logging
import operator
import time
from collections.abc import Iterator
from typing import Annotated, TypedDict

from langgraph.graph import END, START, StateGraph

from mizan.llm.gateway import LLMGateway
from mizan.llm.prompts import (
    EXPLAIN_SYSTEM,
    EXTRACT_SYSTEM,
    JUDGE_SYSTEM,
    REDACT_SYSTEM,
    explain_user_prompt,
    extract_user_prompt,
    judge_user_prompt,
    redact_user_prompt,
)
from mizan.pipeline import redact as redact_mod
from mizan.pipeline.parse import ParsedCV
from mizan.pipeline.score import score as score_fn
from mizan.pipeline.verify import verify as verify_fn
from mizan.schemas.rubric import Rubric
from mizan.schemas.screening import (
    CandidateProfile,
    CriterionJudgment,
    Explanation,
    JudgeDraft,
    ProgressEvent,
    RedactDraft,
    ScoreBreakdown,
    ScreeningResult,
    VerifyStats,
)

log = logging.getLogger("mizan.pipeline")

NODE_ORDER = ("redact", "extract", "judge", "verify", "score", "explain")
# Execution stages: nodes in one stage run in parallel; the next stage starts when all are done.
STAGES: tuple[tuple[str, ...], ...] = (
    ("redact",),
    ("extract", "judge"),
    ("verify",),
    ("score",),
    ("explain",),
)


class ScreenState(TypedDict, total=False):
    # inputs
    rubric: Rubric
    cv: ParsedCV
    blind: bool
    candidate_ref: str
    # working data
    lines: dict[str, str]
    redactions: int
    redact_skipped: bool
    profile: CandidateProfile
    judge_draft: JudgeDraft
    judgments: list[CriterionJudgment]
    verify_stats: VerifyStats
    breakdown: ScoreBreakdown
    explanation: Explanation
    llm_calls: Annotated[int, operator.add]


def _rubric_block(rubric: Rubric) -> str:
    rows = []
    for c in rubric.criteria:
        years = f" | min_years {c.min_years}" if c.min_years else ""
        rows.append(f"{c.id} | {c.type} | weight {c.weight}{years} | {c.name}")
    return "\n".join(rows)


def _judgments_block(judgments: list[CriterionJudgment]) -> str:
    rows = [
        {
            "criterion": j.criterion_name,
            "type": j.criterion_type,
            "verdict": j.verdict,
            "evidence": [e.quote for e in j.evidence],
        }
        for j in judgments
    ]
    return json.dumps(rows, ensure_ascii=False, indent=1)


def build_graph(gateway: LLMGateway):
    def redact(state: ScreenState) -> dict:
        lines = state["cv"].line_map()
        if not state.get("blind"):
            return {"lines": lines, "redactions": 0, "redact_skipped": True, "llm_calls": 0}
        lines, hits = redact_mod.regex_redact(lines)
        res = gateway.complete_json(
            system=REDACT_SYSTEM,
            user=redact_user_prompt(redact_mod.numbered(lines)),
            schema=RedactDraft,
        )
        lines, more = redact_mod.apply_llm_redactions(lines, res.data)
        return {"lines": lines, "redactions": hits + more, "redact_skipped": False, "llm_calls": 1}

    def extract(state: ScreenState) -> dict:
        res = gateway.complete_json(
            system=EXTRACT_SYSTEM,
            user=extract_user_prompt(redact_mod.numbered(state["lines"])),
            schema=CandidateProfile,
        )
        return {"profile": res.data, "llm_calls": 1}

    def judge(state: ScreenState) -> dict:
        res = gateway.complete_json(
            system=JUDGE_SYSTEM,
            user=judge_user_prompt(
                _rubric_block(state["rubric"]), redact_mod.numbered(state["lines"])
            ),
            schema=JudgeDraft,
        )
        return {"judge_draft": res.data, "llm_calls": 1}

    def verify(state: ScreenState) -> dict:
        judgments, stats = verify_fn(state["judge_draft"], state["rubric"], state["lines"])
        return {"judgments": judgments, "verify_stats": stats}

    def score(state: ScreenState) -> dict:
        return {"breakdown": score_fn(state["judgments"])}

    def explain(state: ScreenState) -> dict:
        res = gateway.complete_json(
            system=EXPLAIN_SYSTEM,
            user=explain_user_prompt(
                _judgments_block(state["judgments"]), state["rubric"].language
            ),
            schema=Explanation,
        )
        return {"explanation": res.data, "llm_calls": 1}

    g = StateGraph(ScreenState)
    for name, fn in (
        ("redact", redact),
        ("extract", extract),
        ("judge", judge),
        ("verify", verify),
        ("score", score),
        ("explain", explain),
    ):
        g.add_node(name, fn)
    g.add_edge(START, "redact")
    g.add_edge("redact", "extract")
    g.add_edge("redact", "judge")
    g.add_edge(["extract", "judge"], "verify")  # fan-in: verify waits for both
    g.add_edge("verify", "score")
    g.add_edge("score", "explain")
    g.add_edge("explain", END)
    return g.compile()


def _detail(node: str, update: dict) -> dict:
    """Small, UI-friendly facts about what a node did (never the CV text)."""
    if node == "redact":
        return {"redactions": update.get("redactions", 0)}
    if node == "extract":
        p: CandidateProfile = update["profile"]
        return {"skills": len(p.skills), "experiences": len(p.experiences)}
    if node == "judge":
        return {"judgments": len(update["judge_draft"].judgments)}
    if node == "verify":
        return update["verify_stats"].model_dump()
    if node == "score":
        b: ScoreBreakdown = update["breakdown"]
        return {"score": b.score, "must_haves_met": b.must_haves_met}
    if node == "explain":
        e: Explanation = update["explanation"]
        return {"strengths": len(e.strengths), "gaps": len(e.gaps)}
    return {}


def run_screening(
    gateway: LLMGateway,
    *,
    rubric: Rubric,
    cv: ParsedCV,
    blind: bool,
    candidate_ref: str,
) -> Iterator[ProgressEvent | ScreeningResult]:
    """Yield a ProgressEvent per node, then the final ScreeningResult."""
    started = time.perf_counter()
    graph = build_graph(gateway)
    init: ScreenState = {
        "rubric": rubric,
        "cv": cv,
        "blind": blind,
        "candidate_ref": candidate_ref,
        "llm_calls": 0,
    }
    final: dict = dict(init)
    done: set[str] = set()
    stage_idx = 0
    for node in STAGES[0]:
        yield ProgressEvent(node=node, status="running")
    for chunk in graph.stream(init, stream_mode="updates"):
        for node, update in chunk.items():
            # llm_calls is a counter (reducer = add); every other key is a plain overwrite.
            final.update({k: v for k, v in update.items() if k != "llm_calls"})
            final["llm_calls"] = final.get("llm_calls", 0) + update.get("llm_calls", 0)
            status = "skipped" if node == "redact" and update.get("redact_skipped") else "done"
            yield ProgressEvent(node=node, status=status, detail=_detail(node, update))
            done.add(node)
            # When every node of the current stage is done, announce the next stage.
            while stage_idx < len(STAGES) and set(STAGES[stage_idx]) <= done:
                stage_idx += 1
                if stage_idx < len(STAGES):
                    for nxt in STAGES[stage_idx]:
                        yield ProgressEvent(node=nxt, status="running")

    breakdown: ScoreBreakdown = final["breakdown"]
    explanation: Explanation = final["explanation"]
    duration_ms = int((time.perf_counter() - started) * 1000)
    log.info(
        "screened ref=%s score=%s must_haves_met=%s llm_calls=%s dropped=%s duration_ms=%s",
        candidate_ref,
        breakdown.score,
        breakdown.must_haves_met,
        final["llm_calls"],
        final["verify_stats"].quotes_dropped,
        duration_ms,
    )
    yield ScreeningResult(
        candidate_ref=candidate_ref,
        language=rubric.language,
        blind=blind,
        score=breakdown.score,
        must_haves_met=breakdown.must_haves_met,
        missing_must_haves=breakdown.missing_must_haves,
        judgments=final["judgments"],
        strengths=explanation.strengths,
        gaps=explanation.gaps,
        summary=explanation.summary,
        interview_questions=explanation.interview_questions,
        profile=final["profile"],
        verify=final["verify_stats"],
        line_count=len(cv.lines),
        llm_calls=final["llm_calls"],
        duration_ms=duration_ms,
    )
