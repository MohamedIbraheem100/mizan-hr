# ADR-0002: Groq as primary LLM provider until Gemini free tier is available

**Date:** 2026-11-07 · **Status:** accepted (temporary)

## Context
The locked stack names Gemini as the primary provider and Groq as the fallback (CLAUDE.md, D6).
During M3 the Gemini API returned `403 PERMISSION_DENIED: The Gemini API free tier is not
available for this project` for the owner's key. Google's troubleshooting page states that
free-tier eligibility is decided per Google Cloud project and that creating a new key in the
same project does not help. Upgrading to the paid tier is out (D4: no credit card).
Groq works with `openai/gpt-oss-120b` and produced correct Arabic and English rubrics.

## Decision
- Run with `LLM_PROVIDER=groq` and `LLM_FALLBACK_PROVIDER=gemini` in `.env` and in Vercel
  env vars. No code change: the gateway is provider-agnostic by design.
- Code defaults stay as the locked stack says (Gemini primary) so the intent is documented.
- Revisit when a Gemini key from an eligible project is available; flip the two env vars back.

## Consequences
- Text-only tasks are unaffected. PDF vision for scanned CVs (M4) relied on Gemini; with Groq
  primary, scanned PDFs will be flagged and reported as "no text layer" until Gemini is back.
- The provider swap was a two-line config change, which validates D6 in week one.
