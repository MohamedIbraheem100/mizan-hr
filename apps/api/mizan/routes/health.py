"""Liveness endpoint. Used by docker compose, Vercel, and uptime monitors."""

from fastapi import APIRouter
import os
from mizan import __version__
from mizan.core.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    settings = get_settings()
    return {
        "status": "ok",
        "service": "mizan-api",
        "version": __version__,
        "env": settings.app_env,
    }
