"""The contract every LLM provider must satisfy.

The gateway only knows this interface. Swapping Gemini for Groq (or anything
else) never touches pipeline code: that is decision D6 in the docs.
"""

from typing import Protocol

from pydantic import BaseModel


class ProviderError(Exception):
    """Transport/API failure: network, auth, quota, 5xx. Triggers fallback."""


class LLMProvider(Protocol):
    name: str

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        """Return the model's raw text reply, expected to be one JSON object."""
        ...
