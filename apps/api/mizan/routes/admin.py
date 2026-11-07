"""Operational endpoints. Protected by a shared secret, called by GitHub Actions."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from mizan.core.config import get_settings
from mizan.db.models import ScreeningRow, utcnow
from mizan.db.session import get_db

log = logging.getLogger("mizan.admin")
router = APIRouter(prefix="/admin", tags=["admin"])


def require_token(x_cleanup_token: Annotated[str, Header()] = "") -> None:
    expected = get_settings().cleanup_token
    if not expected or x_cleanup_token != expected:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Forbidden")


@router.post("/cleanup", dependencies=[Depends(require_token)])
def cleanup(db: Annotated[Session, Depends(get_db)]) -> dict[str, int]:
    """Delete screenings past their 24 h retention (results cascade)."""
    now = utcnow()
    expired = db.execute(select(ScreeningRow).where(ScreeningRow.expires_at <= now)).scalars().all()
    ids = [s.id for s in expired]
    if ids:
        db.execute(delete(ScreeningRow).where(ScreeningRow.id.in_(ids)))
        db.commit()
    log.info("cleanup removed=%s", len(ids))
    return {"removed": len(ids)}
