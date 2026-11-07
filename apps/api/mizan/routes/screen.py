"""POST /screen: one CV against a screening's rubric, streamed as Server-Sent Events,
and the verified result persisted.

SSE is plain text over a kept-open HTTP response:

    event: progress
    data: {"node": "judge", "status": "running"}

    event: result
    data: {...ScreeningResult...}

One request per CV (the frontend runs up to 3 in parallel) keeps each call far
under Vercel's function timeout and isolates failures.
"""

import json
import logging
from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette.concurrency import iterate_in_threadpool

from mizan.db import repo
from mizan.db.session import get_db, get_sessionmaker
from mizan.llm.gateway import LLMGateway, LLMUnavailableError, get_gateway
from mizan.pipeline.graph import run_screening
from mizan.pipeline.parse import UnsupportedFileError, parse_file
from mizan.schemas.screening import ProgressEvent, ScreeningResult

log = logging.getLogger("mizan.screen")
router = APIRouter(tags=["screen"])

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB, per the docs' file-validation rule


def sse(event: str, payload: BaseModel | dict) -> str:
    data = payload.model_dump_json() if isinstance(payload, BaseModel) else json.dumps(payload)
    return f"event: {event}\ndata: {data}\n\n"


@router.post("/screen")
async def screen(
    file: Annotated[UploadFile, File(description="CV as .pdf, .docx or .txt (max 5 MB)")],
    screening_id: Annotated[str, Form(description="From POST /screenings")],
    gateway: Annotated[LLMGateway, Depends(get_gateway)],
    db: Annotated[Session, Depends(get_db)],
    candidate_ref: Annotated[str, Form(max_length=60)] = "",
) -> StreamingResponse:
    screening = repo.get_screening(db, screening_id)
    if screening is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Screening not found.")
    if repo.is_expired(screening):
        raise HTTPException(status.HTTP_410_GONE, "This screening has expired.")
    rubric = repo.rubric_of(screening)
    blind = screening.blind

    data = await file.read()
    if len(data) > MAX_UPLOAD_BYTES:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "File larger than 5 MB.")
    try:
        cv = parse_file(file.filename or "cv", data)
    except UnsupportedFileError as exc:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, str(exc)) from exc
    except Exception as exc:  # corrupt file
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, "Could not read this file."
        ) from exc
    if cv.source == "pdf" and not cv.has_text_layer:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT,
            "This PDF has no text layer (scanned image). Upload a text PDF or DOCX; "
            "scanned-PDF support is coming.",
        )
    if not cv.lines:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "The file contains no text.")

    ref = candidate_ref.strip() or f"Candidate #{len(screening.results) + 1}"

    def events() -> Iterator[str]:
        yield sse(
            "progress",
            ProgressEvent(
                node="parse",
                status="done",
                detail={"lines": len(cv.lines), "pages": cv.page_count, "source": cv.source},
            ),
        )
        try:
            for item in run_screening(
                gateway, rubric=rubric, cv=cv, blind=blind, candidate_ref=ref
            ):
                if isinstance(item, ScreeningResult):
                    # This generator runs in a worker thread: it gets its own session.
                    with get_sessionmaker()() as session:
                        repo.save_result(session, screening_id, item)
                    yield sse("result", item)
                else:
                    yield sse("progress", item)
        except LLMUnavailableError as exc:
            log.error("screen failed ref=%s: %s", ref, exc)
            yield sse("error", {"detail": "LLM providers are unavailable. Try again shortly."})
        except Exception:
            log.exception("screen crashed ref=%s", ref)
            yield sse("error", {"detail": "Internal error while screening this CV."})

    return StreamingResponse(
        iterate_in_threadpool(events()),  # pipeline is sync; keep the event loop free
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
