"""FastAPI entrypoint. Run locally with: uvicorn mizan.main:app --reload"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from mizan import __version__
from mizan.routes import health

app = FastAPI(
    title="Mizan API",
    description="AI recruiter: evidence-based CV screening. Decision-support, never auto-reject.",
    version=__version__,
)

# The Next.js app on Vercel calls this API from the browser, so CORS is required.
# Tightened to the real domain in M6.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
