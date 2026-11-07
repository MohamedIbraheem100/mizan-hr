"""Tables. Three of them, and none holds a CV file, CV text or a candidate name.

Privacy rules (CLAUDE.md): persist only scores and quoted evidence; delete
screenings older than 24 h (the `expires_at` column makes that a one-line query).
"""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

RETENTION = timedelta(hours=24)

# JSON everywhere, JSONB on Postgres (indexable, compact). Same model, every DB.
JSONType = JSON().with_variant(JSONB(), "postgresql")


def new_id() -> str:
    return str(uuid.uuid4())


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    pass


class RubricRow(Base):
    """The rubric as CONFIRMED by the recruiter (after editing weights)."""

    __tablename__ = "rubrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    job_title: Mapped[str] = mapped_column(String(120))
    language: Mapped[str] = mapped_column(String(2))
    criteria: Mapped[list] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    screenings: Mapped[list["ScreeningRow"]] = relationship(back_populates="rubric")


class ScreeningRow(Base):
    """One screening session: a rubric, a mode, and up to N results."""

    __tablename__ = "screenings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    rubric_id: Mapped[str] = mapped_column(ForeignKey("rubrics.id", ondelete="CASCADE"))
    blind: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: utcnow() + RETENTION, index=True
    )

    rubric: Mapped[RubricRow] = relationship(back_populates="screenings")
    results: Mapped[list["ResultRow"]] = relationship(
        back_populates="screening", cascade="all, delete-orphan"
    )


class ResultRow(Base):
    """One candidate's verified result. `payload` is the full ScreeningResult JSON."""

    __tablename__ = "results"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    screening_id: Mapped[str] = mapped_column(
        ForeignKey("screenings.id", ondelete="CASCADE"), index=True
    )
    candidate_ref: Mapped[str] = mapped_column(String(60))
    score: Mapped[int] = mapped_column(Integer)
    must_haves_met: Mapped[bool] = mapped_column(Boolean)
    payload: Mapped[dict] = mapped_column(JSONType)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    screening: Mapped[ScreeningRow] = relationship(back_populates="results")
