# ADR-0001: Day-1 MVP scope

**Date:** 2026-11-07 · **Status:** accepted

## Context
`docs/project-documentation.md` describes the full Phase-1 vision. Day-1 must ship a live, demoable MVP
on free tiers without scope creep.

## Decision
Build M0 → M6 as listed in `CLAUDE.md`. Deliberately deferred from the documentation:
- **Match node (embeddings)** between Extract and Judge. Judge works on the raw text; embeddings come later with pgvector.
- **Langfuse** tracing, **UptimeRobot**, `deploy.yml`, **GHCR push**, **Trivy**, **Neon branching per PR**.
- PDF.js in-place highlighting (Day-1 highlights lines in a text view instead).
- Phase 2/3 features (Talent Pool chat, Interview kit, Evaluation dashboard, Two-sided mode).

## Consequences
- Simpler pipeline (7 nodes) and lighter Python bundle for Vercel.
- Every deferred item is tracked here so nothing is silently dropped.
