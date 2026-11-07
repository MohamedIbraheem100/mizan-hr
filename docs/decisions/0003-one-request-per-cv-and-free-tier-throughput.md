# ADR-0003: One request per CV, parallel nodes, and free-tier throughput

**Date:** 2026-11-07 · **Status:** accepted

## Context
The MVP runs on free tiers with no credit card (D4). Screening one CV costs 3 LLM calls
(Extract, Judge, Explain; +1 Redact in Blind mode), roughly 1.5k tokens each. Measured on the
Groq free tier during M4a:

| Fact | Value |
|---|---|
| Rate limit per model (tokens/minute) | 8 000 |
| Usable Groq models for JSON (own buckets) | `openai/gpt-oss-120b`, `openai/gpt-oss-20b`, `qwen/qwen3.8-27b` |
| Tokens for 10 CVs | about 45 000 |
| 10 CVs, 3 in parallel, single model | 220 s (mostly waiting on 429s) |
| 10 CVs, 3-model chain with cooldown, parallel Extract+Judge | about 90 s |

Gemini (1M TPM free) would meet the 60 s target but is unavailable for this account (ADR-0002).

## Decisions
1. **One HTTP request per CV.** The frontend fans out (3 in parallel). Each request streams
   its own SSE events, stays far below Vercel's 300 s limit, and a failing CV never blocks
   the others. More CVs = more requests, never bigger requests.
2. **Extract and Judge run in parallel** inside the LangGraph graph (same superstep). Both
   need only the redacted lines; this removes one call latency per CV at no quality cost.
3. **Provider chain with per-provider cooldown.** `LLM_PROVIDERS` lists several Groq models;
   a model that answers 429 is skipped until its `retry in N s` passes. Traffic flows to the
   next bucket instead of queueing. The gateway only sleeps when nobody is available.
4. **Honest acceptance threshold.** The live ranking test asserts < 120 s on the free tier and
   records 60 s as the target. The public demo serves the sample set from precomputed results
   (Demo mode, M6), so the HR demo never waits on live quotas.

## Scale path (not built now)
- Paid LLM tier or the customer's own key: concurrency 20-50, 100 CVs in under a minute.
- Queue + workers (Redis/QStash) for 50+ CVs: upload, leave, get notified.
- Cache identical (CV, rubric) pairs; batch APIs for overnight bulk runs.
The unit of work (CV = request = independent result) does not change in any of these.
