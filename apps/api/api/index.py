"""Vercel entrypoint.

Vercel's Python runtime looks for an ASGI app named `app` under api/. Every
path is rewritten here by vercel.json, so FastAPI keeps its own routing
(/health, /rubric, /screenings, /screen). Locally you never use this file:
`uvicorn mizan.main:app` runs the same app.
"""

from mizan.main import app  # noqa: F401
