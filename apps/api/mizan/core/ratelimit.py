"""Daily rate limit: N CVs per visitor + a global daily cap.

Backend: Upstash Redis over REST (no redis library, works from serverless).
Fallback: in-process memory when Upstash is not configured (local dev, tests).
Visitor key = SHA-256 of the client IP, truncated: no cookies, no tracking, and
the raw IP is never stored.
"""

import hashlib
import logging
import threading
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache
from typing import Protocol

import httpx

from mizan.core.config import Settings, get_settings

log = logging.getLogger("mizan.ratelimit")

DAY_S = 24 * 3600


class Backend(Protocol):
    def incr_with_ttl(self, key: str, ttl_s: int) -> int: ...


class MemoryBackend:
    def __init__(self) -> None:
        self._data: dict[str, tuple[int, float]] = {}
        self._lock = threading.Lock()

    def incr_with_ttl(self, key: str, ttl_s: int) -> int:
        now = time.time()
        with self._lock:
            count, expires = self._data.get(key, (0, 0.0))
            if expires <= now:
                count, expires = 0, now + ttl_s
            count += 1
            self._data[key] = (count, expires)
            return count


class UpstashBackend:
    """INCR + EXPIRE NX in one pipeline call (one HTTP round trip)."""

    def __init__(self, url: str, token: str, timeout_s: float = 3.0) -> None:
        self._client = httpx.Client(
            base_url=url.rstrip("/"),
            headers={"Authorization": f"Bearer {token}"},
            timeout=timeout_s,
        )

    def incr_with_ttl(self, key: str, ttl_s: int) -> int:
        resp = self._client.post("/pipeline", json=[["INCR", key], ["EXPIRE", key, ttl_s, "NX"]])
        resp.raise_for_status()
        return int(resp.json()[0]["result"])


@dataclass
class Decision:
    allowed: bool
    remaining: int
    limit: int
    scope: str  # "visitor" | "global"


class RateLimiter:
    def __init__(self, per_day: int, global_per_day: int, backend: Backend) -> None:
        self.per_day = per_day
        self.global_per_day = global_per_day
        self.backend = backend

    @staticmethod
    def visitor_key(ip: str) -> str:
        return hashlib.sha256(ip.encode()).hexdigest()[:16]

    def check(self, ip: str) -> Decision:
        day = datetime.now(UTC).strftime("%Y%m%d")
        try:
            g = self.backend.incr_with_ttl(f"rl:global:{day}", DAY_S)
            if g > self.global_per_day:
                return Decision(False, 0, self.global_per_day, "global")
            v = self.backend.incr_with_ttl(f"rl:v:{self.visitor_key(ip)}:{day}", DAY_S)
            if v > self.per_day:
                return Decision(False, 0, self.per_day, "visitor")
            return Decision(True, self.per_day - v, self.per_day, "visitor")
        except Exception as exc:  # Redis down must not take the product down
            log.warning("rate limit backend error, allowing request: %s", exc)
            return Decision(True, -1, self.per_day, "visitor")


def build_limiter(settings: Settings) -> RateLimiter:
    if settings.upstash_redis_rest_url and settings.upstash_redis_rest_token:
        backend: Backend = UpstashBackend(
            settings.upstash_redis_rest_url, settings.upstash_redis_rest_token
        )
    else:
        log.warning("UPSTASH not configured: rate limit uses in-memory counters")
        backend = MemoryBackend()
    return RateLimiter(settings.rate_limit_per_day, settings.rate_limit_global_per_day, backend)


@lru_cache
def get_limiter() -> RateLimiter:
    return build_limiter(get_settings())


def client_ip(headers: dict[str, str] | None, fallback: str) -> str:
    """Vercel sets x-forwarded-for; the first hop is the client."""
    xff = (headers or {}).get("x-forwarded-for", "")
    return xff.split(",")[0].strip() or fallback
