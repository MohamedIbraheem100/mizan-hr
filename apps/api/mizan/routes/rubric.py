"""POST /rubric: job description text -> proposed Rubric (editable by the recruiter)."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from mizan.llm.gateway import LLMGateway, LLMUnavailableError, get_gateway
from mizan.llm.prompts import RUBRIC_SYSTEM, rubric_user_prompt
from mizan.schemas.rubric import Rubric, RubricDraft, RubricRequest

log = logging.getLogger("mizan.rubric")
router = APIRouter(tags=["rubric"])


@router.post("/rubric", response_model=Rubric)
def create_rubric(
    req: RubricRequest, gateway: Annotated[LLMGateway, Depends(get_gateway)]
) -> Rubric:
    try:
        result = gateway.complete_json(
            system=RUBRIC_SYSTEM, user=rubric_user_prompt(req.jd_text), schema=RubricDraft
        )
    except LLMUnavailableError as exc:
        log.error("rubric failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM providers are unavailable right now. Try again in a minute.",
        ) from exc
    try:
        rubric = result.data.to_rubric()  # code assigns ids + normalizes weights
    except ValueError as exc:
        # Model returned a shape we accept syntactically but reject semantically.
        log.error("rubric rejected by validators: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model returned an unusable rubric. Try rephrasing the job description.",
        ) from exc
    log.info("rubric ok provider=%s criteria=%s", result.provider, len(rubric.criteria))
    return rubric
