"""Screening sessions.

POST /screenings        recruiter confirms the (edited) rubric -> screening_id
GET  /screenings/{id}   rubric + ranked results (410 once the 24 h retention passed)
"""

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from mizan.db import repo
from mizan.db.session import get_db
from mizan.schemas.rubric import Rubric
from mizan.schemas.screening import ScreeningResult

router = APIRouter(tags=["screenings"])


class CreateScreeningRequest(BaseModel):
    rubric: Rubric
    blind: bool = Field(default=True, description="Blind mode is on by default in the demo")


class ScreeningCreated(BaseModel):
    screening_id: str
    blind: bool
    expires_at: datetime


class ScreeningView(BaseModel):
    screening_id: str
    rubric: Rubric
    blind: bool
    created_at: datetime
    expires_at: datetime
    results: list[ScreeningResult]


@router.post("/screenings", response_model=ScreeningCreated, status_code=status.HTTP_201_CREATED)
def create_screening(
    req: CreateScreeningRequest, db: Annotated[Session, Depends(get_db)]
) -> ScreeningCreated:
    row = repo.create_screening(db, req.rubric, req.blind)
    return ScreeningCreated(screening_id=row.id, blind=row.blind, expires_at=row.expires_at)


@router.get("/screenings/{screening_id}", response_model=ScreeningView)
def get_screening(screening_id: str, db: Annotated[Session, Depends(get_db)]) -> ScreeningView:
    row = repo.get_screening(db, screening_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Screening not found.")
    if repo.is_expired(row):
        raise HTTPException(
            status.HTTP_410_GONE, "This screening has expired (results are kept for 24 hours)."
        )
    return ScreeningView(
        screening_id=row.id,
        rubric=repo.rubric_of(row),
        blind=row.blind,
        created_at=row.created_at,
        expires_at=row.expires_at,
        results=repo.ranked_results(row),
    )
