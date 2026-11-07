"""Score node: CODE, not LLM.

met = 1, partial = 0.5, not_met / no_evidence = 0
score = sum(weight * value) / sum(weight) * 100
A missing must-have FLAGS the candidate; it never removes them (decision-support).
"""

from mizan.schemas.screening import VERDICT_VALUE, CriterionJudgment, ScoreBreakdown


def score(judgments: list[CriterionJudgment]) -> ScoreBreakdown:
    weight_total = sum(j.weight for j in judgments)
    weighted_sum = sum(j.weight * VERDICT_VALUE[j.verdict] for j in judgments)
    pct = round(weighted_sum / weight_total * 100) if weight_total > 0 else 0
    missing = [
        j.criterion_name
        for j in judgments
        if j.criterion_type == "must_have" and j.verdict != "met"
    ]
    return ScoreBreakdown(
        score=max(0, min(100, pct)),
        weighted_sum=round(weighted_sum, 4),
        weight_total=round(weight_total, 4),
        must_haves_met=not missing,
        missing_must_haves=missing,
    )
