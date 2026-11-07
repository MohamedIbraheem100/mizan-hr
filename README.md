# Mizan ⚖️ — AI Recruiter

> **Live demo:** _coming soon_ · **Status:** Day-1 MVP in progress

Mizan screens CVs against a Job Description in minutes and shows **why** every score was given:
each criterion is backed by a quoted line from the CV itself.

Mizan is a **decision-support tool**. The recruiter always makes the final decision. No auto-reject, ever.

## What it does
1. Paste a Job Description (Arabic or English).
2. Mizan proposes an editable **Rubric** (must-have / nice-to-have, with weights).
3. Upload CVs (PDF / DOCX). Each CV is screened against the rubric.
4. Get a **ranked list** where every score links to the exact CV line that justifies it.
5. **Blind mode** hides name, age, gender, nationality and photo before scoring.

## Stack
| Layer | Choice |
|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui → Vercel |
| Backend | Python 3.12 + FastAPI + Pydantic v2 → Vercel Python Functions |
| Orchestration | LangGraph |
| LLM | Provider-agnostic gateway: Gemini → Groq → OpenAI (optional) |
| DB | Neon Postgres (+ pgvector) via SQLAlchemy + Alembic |
| Rate limit | Upstash Redis |
| CI | GitHub Actions |
| Local dev | docker compose: api + postgres + redis |

## Run locally
```bash
cp .env.example .env        # fill in your keys
docker compose up --build   # api on http://localhost:8000, /health
```
Web app:
```bash
cd apps/web && npm install && npm run dev   # http://localhost:3000
```

## Repo layout
```
apps/web/     Next.js frontend
apps/api/     FastAPI backend (pipeline, llm gateway, routes)
data/         synthetic sample CVs and JDs (ar + en)
docs/         architecture, decisions (ADRs), project documentation
```

## Privacy
CV files are never stored. Only scores and quoted evidence are persisted, and screenings are deleted after 24 hours.
The public demo uses **synthetic** CVs only. Do not upload real candidates' CVs.

## Docs
- [Project documentation](docs/project-documentation.md)
- [Architecture](docs/architecture.md)
- [Decisions (ADRs)](docs/decisions/)
- [From zero to production: study guide (Arabic)](docs/from-zero-to-production.md)
