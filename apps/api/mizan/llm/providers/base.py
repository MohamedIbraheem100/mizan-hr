"""The contract every LLM provider must satisfy.

The gateway only knows this interface. Swapping Gemini for Groq (or anything
else) never touches pipeline code: that is decision D6 in the docs.
"""

import re
from typing import Protocol

from pydantic import BaseModel

_RETRY_PATTERNS = (
    re.compile(r"try again in ([\d.]+)\s*(ms|s)\b", re.I),  # groq
    re.compile(r"retry in ([\d.]+)\s*(s)\b", re.I),  # gemini "Please retry in 23.4s"
    re.compile(r"retryDelay['\"]?\s*:\s*['\"]?([\d.]+)(s)", re.I),  # gemini JSON detail
)


def parse_retry_after(text: str) -> float | None:
    """Seconds the provider asked us to wait, if its error message says so."""
    for pat in _RETRY_PATTERNS:
        m = pat.search(text)
        if m:
            value, unit = float(m.group(1)), m.group(2).lower()
            return value / 1000 if unit == "ms" else value
    return None


class ProviderError(Exception):
    """Transport/API failure: network, auth, quota, 5xx.

    `retry_after_s` is set for rate limits that say when to retry; the gateway may
    wait that long and try the same provider once more instead of falling back.
    """

    def __init__(self, message: str, *, retry_after_s: float | None = None) -> None:
        super().__init__(message)
        self.retry_after_s = retry_after_s


class LLMProvider(Protocol):
    name: str

    def generate_json(
        self, *, system: str, user: str, schema: type[BaseModel], timeout_s: float
    ) -> str:
        """Return the model's raw text reply, expected to be one JSON object."""
        ...
