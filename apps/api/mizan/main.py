"""FastAPI entrypoint. Run locally with: uvicorn mizan.main:app --reload"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mizan import __version__
from mizan.core.config import get_settings
from mizan.core.logging import configure_logging
from mizan.routes import admin, health, rubric, screen, screenings

configure_logging(get_settings().log_level)

app = FastAPI(
    title="Mizan API",
    description="AI recruiter: evidence-based CV screening. Decision-support, never auto-reject.",
    version=__version__,
)

# The Next.js app on Vercel calls this API from the browser, so CORS is required.
# Allowed: the production site, Vercel preview URLs of the web project, local dev.
_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in _settings.cors_origins.split(",") if o.strip()],
    allow_origin_regex=_settings.cors_origin_regex or None,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(rubric.router)
app.include_router(screenings.router)
app.include_router(screen.router)
app.include_router(admin.router)
