"""Gemini provider (primary). Uses native structured output."""

from google import genai
from google.genai import types
from pydantic import BaseModel

from mizan.llm.providers.base import ProviderError


class GeminiProvider:
    name = "gemini"

    def __init__(self, api_key: str, model: str, timeout_s: float = 60.0) -> None:
        if not api_key:
            raise ProviderError("gemini: GEMINI_API_KEY is not set")
        self._model = model
        self._client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(timeout=int(timeout_s * 1000)),  # milliseconds
        )

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        try:
            resp = self._client.models.generate_content(
                model=self._model,
                contents=user,
                config=types.GenerateContentConfig(
                    system_instruction=system,
                    response_mime_type="application/json",
                    response_schema=schema,
                    temperature=0,
                ),
            )
        except Exception as exc:  # the SDK raises many types; all mean "try the fallback"
            raise ProviderError(f"gemini: {type(exc).__name__}: {exc}") from exc
        return resp.text or ""
