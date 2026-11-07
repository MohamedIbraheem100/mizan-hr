"""Rubric: what the recruiter screens CVs against.

The LLM proposes criteria; CODE assigns ids and normalizes weights.
Never trust the model to do arithmetic or bookkeeping.
"""

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CriterionType = Literal["must_have", "nice_to_have"]
Language = Literal["ar", "en"]


class Criterion(BaseModel):
    id: str = Field(default="", description="Assigned by code: c1, c2, ...")
    name: str = Field(min_length=2, max_length=120)
    type: CriterionType
    weight: float = Field(gt=0, le=1)
    min_years: int | None = Field(default=None, ge=0, le=40)
    description: str = Field(default="", max_length=300)


class Rubric(BaseModel):
    job_title: str = Field(min_length=2, max_length=120)
    language: Language
    criteria: list[Criterion] = Field(min_length=1, max_length=12)

    @field_validator("criteria")
    @classmethod
    def _at_least_one_must_have(cls, criteria: list[Criterion]) -> list[Criterion]:
        if not any(c.type == "must_have" for c in criteria):
            raise ValueError("rubric needs at least one must_have criterion")
        return criteria

    @model_validator(mode="after")
    def _assign_ids_and_normalize_weights(self) -> "Rubric":
        total = sum(c.weight for c in self.criteria)
        for i, c in enumerate(self.criteria, start=1):
            c.id = f"c{i}"
            c.weight = round(c.weight / total, 4)
        return self


# ---- LLM-facing shape (what we ask the model to produce) ----
# Kept separate so the model never sees/produces `id`, and so prompt changes
# don't leak into the public API schema.
class CriterionDraft(BaseModel):
    name: str
    type: CriterionType
    weight: float
    min_years: int | None = None
    description: str = ""


class RubricDraft(BaseModel):
    job_title: str
    language: Language
    criteria: list[CriterionDraft]

    def to_rubric(self) -> Rubric:
        return Rubric.model_validate(self.model_dump())


# ---- API request ----
class RubricRequest(BaseModel):
    jd_text: str = Field(min_length=30, max_length=10_000, description="Job description, ar or en")
