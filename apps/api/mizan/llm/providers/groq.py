"""Groq provider (fallback). OpenAI-compatible chat API with JSON mode."""

import json

from groq import BadRequestError, Groq
from pydantic import BaseModel

from mizan.llm.providers.base import ProviderError


class GroqProvider:
    name = "groq"

    def __init__(self, api_key: str, model: str, timeout_s: float = 60.0) -> None:
        if not api_key:
            raise ProviderError("groq: GROQ_API_KEY is not set")
        self._model = model
        self._client = Groq(api_key=api_key, timeout=timeout_s)

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        # JSON mode guarantees syntactically valid JSON but not our shape,
        # so we also hand the model the schema. Validation happens in the gateway.
        system_with_schema = (
            f"{system}\n\nRespond with exactly one JSON object that matches this JSON Schema:\n"
            f"{json.dumps(schema.model_json_schema(), ensure_ascii=False)}"
        )
        try:
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system_with_schema},
                    {"role": "user", "content": user},
                ],
                response_format={"type": "json_object"},
                temperature=0,
                timeout=timeout_s,
            )
        except BadRequestError as exc:
            # JSON mode rejected the model's own text (often a refusal like "I can't
            # comply"). That is bad OUTPUT, not a transport failure: hand the text back
            # so the gateway validates it, fails, and retries once with feedback.
            failed = _failed_generation(exc)
            if failed is not None:
                return failed
            raise ProviderError(f"groq: {type(exc).__name__}: {exc}") from exc
        except Exception as exc:
            raise ProviderError(f"groq: {type(exc).__name__}: {exc}") from exc
        return resp.choices[0].message.content or ""


def _failed_generation(exc: BadRequestError) -> str | None:
    body = exc.body if isinstance(exc.body, dict) else {}
    err = body.get("error", body) if isinstance(body, dict) else {}
    if isinstance(err, dict) and err.get("code") == "json_validate_failed":
        return str(err.get("failed_generation", ""))
    return None
