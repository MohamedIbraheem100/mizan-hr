"""The few queries Mizan needs, in one place (routes stay thin)."""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from mizan.db.models import ResultRow, RubricRow, ScreeningRow, utcnow
from mizan.schemas.rubric import Rubric
from mizan.schemas.screening import ScreeningResult


def create_screening(db: Session, rubric: Rubric, blind: bool) -> ScreeningRow:
    rubric_row = RubricRow(
        job_title=rubric.job_title,
        language=rubric.language,
        criteria=[c.model_dump() for c in rubric.criteria],
    )
    screening = ScreeningRow(rubric=rubric_row, blind=blind)
    db.add(screening)
    db.commit()
    db.refresh(screening)
    return screening


def get_screening(db: Session, screening_id: str) -> ScreeningRow | None:
    stmt = (
        select(ScreeningRow)
        .where(ScreeningRow.id == screening_id)
        .options(selectinload(ScreeningRow.rubric), selectinload(ScreeningRow.results))
    )
    return db.execute(stmt).scalar_one_or_none()


def is_expired(screening: ScreeningRow, now: datetime | None = None) -> bool:
    now = now or utcnow()
    expires = screening.expires_at
    if expires.tzinfo is None:  # SQLite drops tzinfo; treat stored values as UTC
        expires = expires.replace(tzinfo=now.tzinfo)
    return expires <= now


def rubric_of(screening: ScreeningRow) -> Rubric:
    r = screening.rubric
    return Rubric.model_validate(
        {"job_title": r.job_title, "language": r.language, "criteria": r.criteria}
    )


def save_result(db: Session, screening_id: str, result: ScreeningResult) -> ResultRow:
    row = ResultRow(
        screening_id=screening_id,
        candidate_ref=result.candidate_ref,
        score=result.score,
        must_haves_met=result.must_haves_met,
        payload=result.model_dump(mode="json"),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def ranked_results(screening: ScreeningRow) -> list[ScreeningResult]:
    """Must-haves met first, then score. A flagged candidate is never removed."""
    rows = sorted(screening.results, key=lambda r: (r.must_haves_met, r.score), reverse=True)
    return [ScreeningResult.model_validate(r.payload) for r in rows]
