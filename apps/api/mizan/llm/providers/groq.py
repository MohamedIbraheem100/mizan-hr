"""Groq provider. OpenAI-compatible chat API with JSON mode.

Free-tier note: Groq rate-limits PER MODEL (tokens per minute), so the same key
can be configured several times with different models and each entry gets its
own bucket. See LLM_PROVIDERS in .env.example.
"""

import json

from groq import BadRequestError, Groq, RateLimitError
from pydantic import BaseModel

from mizan.llm.providers.base import ProviderError, parse_retry_after

_SUPPORTS_REASONING_EFFORT = ("openai/gpt-oss",)


class GroqProvider:
    def __init__(
        self,
        api_key: str,
        model: str,
        timeout_s: float = 60.0,
        reasoning_effort: str | None = "low",
    ) -> None:
        if not api_key:
            raise ProviderError("groq: GROQ_API_KEY is not set")
        self.name = f"groq:{model}"
        self._model = model
        self._client = Groq(api_key=api_key, timeout=timeout_s)
        self._extra: dict = {}
        if reasoning_effort and model.startswith(_SUPPORTS_REASONING_EFFORT):
            self._extra["reasoning_effort"] = reasoning_effort

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        # JSON mode guarantees syntactically valid JSON but not our shape,
        # so we also hand the model the schema. Validation happens in the gateway.
        schema_json = json.dumps(
            _compact(schema.model_json_schema()), ensure_ascii=False, separators=(",", ":")
        )
        system_with_schema = (
            f"{system}\n\nRespond with exactly one JSON object that matches this JSON Schema:\n"
            f"{schema_json}"
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
                **self._extra,
            )
        except RateLimitError as exc:
            raise ProviderError(
                f"{self.name}: RateLimitError: {exc}", retry_after_s=parse_retry_after(str(exc))
            ) from exc
        except BadRequestError as exc:
            # JSON mode rejected the model's own text (often a refusal like "I can't
            # comply"). That is bad OUTPUT, not a transport failure: hand the text back
            # so the gateway validates it, fails, and retries once with feedback.
            failed = _failed_generation(exc)
            if failed is not None:
                return failed
            raise ProviderError(f"{self.name}: {type(exc).__name__}: {exc}") from exc
        except Exception as exc:
            raise ProviderError(f"{self.name}: {type(exc).__name__}: {exc}") from exc
        return resp.choices[0].message.content or ""


def _compact(node):
    """Drop auto-generated 'title' keys from a JSON Schema: pure token cost, zero guidance.
    (Field descriptions are kept; they carry real instructions.)"""
    if isinstance(node, dict):
        return {k: _compact(v) for k, v in node.items() if k != "title"}
    if isinstance(node, list):
        return [_compact(v) for v in node]
    return node


def _failed_generation(exc: BadRequestError) -> str | None:
    body = exc.body if isinstance(exc.body, dict) else {}
    err = body.get("error", body) if isinstance(body, dict) else {}
    if isinstance(err, dict) and err.get("code") == "json_validate_failed":
        return str(err.get("failed_generation", ""))
    return None
