from datetime import timedelta

from fastapi.testclient import TestClient

from mizan.core.config import get_settings
from mizan.core.ratelimit import MemoryBackend, RateLimiter, client_ip, get_limiter
from mizan.db.models import ScreeningRow, utcnow
from mizan.db.session import get_sessionmaker
from mizan.llm.gateway import LLMGateway, get_gateway
from mizan.main import app
from tests.conftest import FakeProvider
from tests.pipeline_fixtures import (
    CV_LINES_EN,
    EXPLAIN_REPLY,
    JUDGE_REPLY_HONEST,
    PROFILE_REPLY,
    RUBRIC,
)


def test_visitor_limit_then_global_cap():
    rl = RateLimiter(per_day=2, global_per_day=3, backend=MemoryBackend())
    assert rl.check("1.1.1.1").allowed and rl.check("1.1.1.1").allowed
    third = rl.check("1.1.1.1")
    assert not third.allowed and third.scope == "visitor"
    # the global counter also counted the rejected attempt: 3 used -> next visitor is capped
    fourth = rl.check("2.2.2.2")
    assert not fourth.allowed and fourth.scope == "global"


def test_backend_failure_fails_open():
    class Broken:
        def incr_with_ttl(self, key, ttl_s):
            raise RuntimeError("redis down")

    assert RateLimiter(1, 1, Broken()).check("1.1.1.1").allowed is True


def test_client_ip_prefers_first_forwarded_hop():
    assert client_ip({"x-forwarded-for": "9.9.9.9, 10.0.0.1"}, "127.0.0.1") == "9.9.9.9"
    assert client_ip({}, "127.0.0.1") == "127.0.0.1"


def test_screen_returns_429_when_over_limit():
    app.dependency_overrides[get_gateway] = lambda: LLMGateway(
        [
            FakeProvider(
                "fake",
                {
                    "CandidateProfile": [PROFILE_REPLY] * 3,
                    "JudgeDraft": [JUDGE_REPLY_HONEST] * 3,
                    "Explanation": [EXPLAIN_REPLY] * 3,
                },
            )
        ]
    )
    limiter = RateLimiter(1, 100, MemoryBackend())  # one instance: counters must persist
    app.dependency_overrides[get_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        sid = client.post("/screenings", json={"rubric": RUBRIC}).json()["screening_id"]
        body = "\n".join(CV_LINES_EN).encode()
        first = client.post("/screen", files={"file": ("a.txt", body)}, data={"screening_id": sid})
        second = client.post("/screen", files={"file": ("b.txt", body)}, data={"screening_id": sid})
        assert first.status_code == 200
        assert second.status_code == 429
        assert "Daily limit" in second.json()["detail"]
        assert second.headers["retry-after"] == "3600"
    finally:
        app.dependency_overrides.clear()


def test_internal_bucket_is_separate_from_visitor_and_global():
    rl = RateLimiter(per_day=1, global_per_day=1, backend=MemoryBackend())
    assert rl.check_internal(2).allowed and rl.check_internal(2).allowed
    third = rl.check_internal(2)
    assert not third.allowed and third.scope == "internal"
    # the public counters were not touched by the internal calls
    assert rl.check("1.1.1.1").allowed


def test_screen_internal_key_skips_visitor_limit_and_has_its_own_cap():
    settings = get_settings()
    settings.internal_key = "portfolio-key"
    settings.rate_limit_internal_per_day = 2
    app.dependency_overrides[get_gateway] = lambda: LLMGateway(
        [
            FakeProvider(
                "fake",
                {
                    "CandidateProfile": [PROFILE_REPLY] * 6,
                    "JudgeDraft": [JUDGE_REPLY_HONEST] * 6,
                    "Explanation": [EXPLAIN_REPLY] * 6,
                },
            )
        ]
    )
    limiter = RateLimiter(1, 100, MemoryBackend())  # visitor limit of ONE
    app.dependency_overrides[get_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        sid = client.post("/screenings", json={"rubric": RUBRIC}).json()["screening_id"]
        body = "\n".join(CV_LINES_EN).encode()

        def screen(headers=None):
            return client.post(
                "/screen",
                files={"file": ("cv.txt", body)},
                data={"screening_id": sid},
                headers=headers or {},
            )

        key = {"X-Internal-Key": "portfolio-key"}
        # two internal calls pass although the visitor limit is one
        assert screen(key).status_code == 200
        assert screen(key).status_code == 200
        # the internal cap (2) then applies, with its own message
        capped = screen(key)
        assert capped.status_code == 429
        assert "partner integration" in capped.json()["detail"]
        # a wrong key is just a normal visitor: first call allowed, second hits the visitor limit
        assert screen({"X-Internal-Key": "wrong"}).status_code == 200
        blocked = screen({"X-Internal-Key": "wrong"})
        assert blocked.status_code == 429 and "Daily limit" in blocked.json()["detail"]
    finally:
        app.dependency_overrides.clear()
        settings.internal_key = ""
        settings.rate_limit_internal_per_day = 100


def test_screen_ignores_internal_key_when_feature_is_off():
    settings = get_settings()
    assert settings.internal_key == ""
    app.dependency_overrides[get_gateway] = lambda: LLMGateway(
        [
            FakeProvider(
                "fake",
                {
                    "CandidateProfile": [PROFILE_REPLY] * 3,
                    "JudgeDraft": [JUDGE_REPLY_HONEST] * 3,
                    "Explanation": [EXPLAIN_REPLY] * 3,
                },
            )
        ]
    )
    limiter = RateLimiter(1, 100, MemoryBackend())
    app.dependency_overrides[get_limiter] = lambda: limiter
    try:
        client = TestClient(app)
        sid = client.post("/screenings", json={"rubric": RUBRIC}).json()["screening_id"]
        body = "\n".join(CV_LINES_EN).encode()
        args = {"files": {"file": ("cv.txt", body)}, "data": {"screening_id": sid}}
        # an empty configured key never matches, even an empty header
        assert client.post("/screen", headers={"X-Internal-Key": ""}, **args).status_code == 200
        assert client.post("/screen", headers={"X-Internal-Key": ""}, **args).status_code == 429
    finally:
        app.dependency_overrides.clear()


def test_admin_cleanup_requires_token_and_deletes_expired():
    settings = get_settings()
    settings.cleanup_token = "test-token"
    client = TestClient(app)
    keep = client.post("/screenings", json={"rubric": RUBRIC}).json()["screening_id"]
    gone = client.post("/screenings", json={"rubric": RUBRIC}).json()["screening_id"]
    with get_sessionmaker()() as db:
        row = db.get(ScreeningRow, gone)
        row.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()

    assert client.post("/admin/cleanup").status_code == 403
    assert client.post("/admin/cleanup", headers={"X-Cleanup-Token": "wrong"}).status_code == 403
    ok = client.post("/admin/cleanup", headers={"X-Cleanup-Token": "test-token"})
    assert ok.status_code == 200 and ok.json() == {"removed": 1}
    assert client.get(f"/screenings/{gone}").status_code == 404
    assert client.get(f"/screenings/{keep}").status_code == 200
    settings.cleanup_token = ""
