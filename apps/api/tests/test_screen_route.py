import json

from fastapi.testclient import TestClient

from mizan.llm.gateway import LLMGateway, get_gateway
from mizan.main import app
from tests.conftest import FakeProvider
from tests.pipeline_fixtures import (
    CV_LINES_EN,
    EXPLAIN_REPLY,
    JUDGE_REPLY_HONEST,
    PROFILE_REPLY,
    RUBRIC,
    docx_bytes,
)
from tests.test_parse import _pdf

SCRIPTED = {
    "CandidateProfile": [PROFILE_REPLY],
    "JudgeDraft": [JUDGE_REPLY_HONEST],
    "Explanation": [EXPLAIN_REPLY],
}


def _client(scripted: dict | None = None) -> TestClient:
    app.dependency_overrides[get_gateway] = lambda: LLMGateway(
        [FakeProvider("fake", scripted or {})]
    )
    return TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def _parse_sse(text: str) -> list[tuple[str, dict]]:
    out = []
    for block in text.strip().split("\n\n"):
        event, data = None, None
        for line in block.splitlines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
        out.append((event, data))
    return out


def _post(client, filename, content, **form):
    return client.post(
        "/screen",
        files={"file": (filename, content, "application/octet-stream")},
        data={"rubric": json.dumps(RUBRIC), **form},
    )


def test_screen_streams_progress_then_result():
    client = _client(SCRIPTED)
    resp = _post(client, "cv.docx", docx_bytes(CV_LINES_EN), candidate_ref="Candidate #7")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(resp.text)
    assert events[0] == (
        "progress",
        {"node": "parse", "status": "done", "detail": {"lines": 9, "pages": 1, "source": "docx"}},
    )
    assert [e for e, _ in events].count("result") == 1
    assert events[-1][0] == "result"
    result = events[-1][1]
    assert result["candidate_ref"] == "Candidate #7"
    assert result["score"] == 100
    assert result["judgments"][0]["evidence"][0]["line_id"] == "L4"


def test_scanned_pdf_is_rejected_with_a_clear_message():
    client = _client()
    resp = _post(client, "scan.pdf", _pdf([]))
    assert resp.status_code == 422
    assert "no text layer" in resp.json()["detail"]


def test_unsupported_extension_is_415():
    client = _client()
    resp = _post(client, "cv.exe", b"MZ....")
    assert resp.status_code == 415


def test_invalid_rubric_is_422():
    client = _client()
    resp = client.post(
        "/screen",
        files={"file": ("cv.txt", b"some cv text here", "text/plain")},
        data={"rubric": json.dumps({"job_title": "x"})},
    )
    assert resp.status_code == 422
    assert "Invalid rubric" in resp.json()["detail"]


def test_oversized_upload_is_413():
    client = _client()
    resp = _post(client, "cv.txt", b"x" * (5 * 1024 * 1024 + 1))
    assert resp.status_code == 413


def test_llm_outage_is_reported_as_an_sse_error_event(down_provider):
    app.dependency_overrides[get_gateway] = lambda: LLMGateway([down_provider])
    client = TestClient(app)
    resp = _post(client, "cv.txt", "\n".join(CV_LINES_EN).encode())
    assert resp.status_code == 200  # headers already sent; the error travels in-stream
    events = _parse_sse(resp.text)
    assert events[-1][0] == "error"
    assert "unavailable" in events[-1][1]["detail"]
