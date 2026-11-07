# Architecture

Serverless: no server to manage. Each CV is processed in its own function call so we stay under
Vercel Hobby's 300 s limit, and one failing CV never blocks the others.

## Components
| Component | Where | Role |
|---|---|---|
| Web (Next.js) | Vercel CDN | UI, static, never sleeps |
| API (FastAPI) | Vercel Python Functions | `/health`, `/rubric`, `/screen`, `/results` |
| Pipeline (LangGraph) | inside the API | Parse → Redact → Extract → Judge → Verify → Score → Explain |
| LLM Gateway | inside the API | one interface, provider via env, fallback chain |
| Neon Postgres (+pgvector) | managed | rubrics, screenings, results |
| Upstash Redis | managed | rate limit + cache |
| Local dev | docker compose | api + postgres(pgvector) + redis |

## Pipeline nodes (Day-1)
1. **Parse** — pypdf / python-docx → numbered lines `L1..Ln`. Scanned PDF → LLM vision.
2. **Redact** (Blind mode) — strip name, age/DOB, gender, nationality, photo refs, marital status, religion.
3. **Extract** — LLM → `CandidateProfile` (structured JSON).
4. **Judge** — per criterion: `met | partial | not_met | no_evidence` + evidence `[{line_id, quote}]`.
5. **Verify** — CODE: each quote must exist (normalized, fuzzy ≥ 0.9) in the cited line, else `no_evidence`.
6. **Score** — CODE: met=1, partial=0.5, else 0. `score = Σ(weight×value)/Σweight×100`. Missing must-have → flag, never remove.
7. **Explain** — LLM → strengths, gaps, 2-line summary in the JD's language.

Every node emits a progress event; `/screen` streams them (SSE) for "Watch Mizan Think".

## Data flow (one screening)
1. Recruiter pastes JD → API returns a proposed Rubric.
2. Recruiter edits weights and confirms → Rubric saved → `screening_id`.
3. Frontend uploads CVs and sends **one request per CV** (max 3 in parallel).
4. Each request runs the pipeline and streams events.
5. Scores + evidence saved; the CV file itself is **never stored**.
6. Frontend shows ranking; evidence highlighting happens in the browser.

## Security
- CV text is untrusted: wrapped in delimiters, instructions inside it are ignored.
- Prompt-injection test CV lives in the test suite and must not score high.
- Rate limit: 10 CVs / visitor / day + global daily cap.
