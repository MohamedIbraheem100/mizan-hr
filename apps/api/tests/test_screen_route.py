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


def _screening(client: TestClient, blind: bool = False) -> str:
    resp = client.post("/screenings", json={"rubric": RUBRIC, "blind": blind})
    assert resp.status_code == 201, resp.text
    return resp.json()["screening_id"]


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


def _post(client, screening_id, filename, content, **form):
    return client.post(
        "/screen",
        files={"file": (filename, content, "application/octet-stream")},
        data={"screening_id": screening_id, **form},
    )


def test_screen_streams_progress_then_result_and_persists_it():
    client = _client(SCRIPTED)
    sid = _screening(client)
    resp = _post(client, sid, "cv.docx", docx_bytes(CV_LINES_EN), candidate_ref="Candidate #7")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/event-stream")
    events = _parse_sse(resp.text)
    assert events[0] == (
        "progress",
        {"node": "parse", "status": "done", "detail": {"lines": 9, "pages": 1, "source": "docx"}},
    )
    assert events[-1][0] == "result"
    result = events[-1][1]
    assert result["candidate_ref"] == "Candidate #7" and result["score"] == 100

    # The result is now readable from the screening, ranked.
    view = client.get(f"/screenings/{sid}").json()
    assert len(view["results"]) == 1
    assert view["results"][0]["candidate_ref"] == "Candidate #7"
    assert view["results"][0]["judgments"][0]["evidence"][0]["line_id"] == "L4"


def test_candidate_ref_defaults_to_a_counter():
    client = _client(SCRIPTED)
    sid = _screening(client)
    events = _parse_sse(_post(client, sid, "cv.txt", "\n".join(CV_LINES_EN).encode()).text)
    assert events[-1][1]["candidate_ref"] == "Candidate #1"


def test_screen_uses_the_screenings_blind_setting():
    scripted = dict(SCRIPTED, RedactDraft=[{"person_names": ["Ahmed Hassan"]}])
    client = _client(scripted)
    sid = _screening(client, blind=True)
    events = _parse_sse(_post(client, sid, "cv.txt", "\n".join(CV_LINES_EN).encode()).text)
    progress = [(e["node"], e["status"]) for n, e in events if n == "progress"]
    assert ("redact", "done") in progress
    assert events[-1][1]["blind"] is True


def test_unknown_screening_is_404():
    client = _client()
    assert _post(client, "nope", "cv.txt", b"some cv text here").status_code == 404


def test_scanned_pdf_is_rejected_with_a_clear_message():
    client = _client()
    resp = _post(client, _screening(client), "scan.pdf", _pdf([]))
    assert resp.status_code == 422
    assert "no text layer" in resp.json()["detail"]


def test_unsupported_extension_is_415():
    client = _client()
    assert _post(client, _screening(client), "cv.exe", b"MZ....").status_code == 415


def test_oversized_upload_is_413():
    client = _client()
    resp = _post(client, _screening(client), "cv.txt", b"x" * (5 * 1024 * 1024 + 1))
    assert resp.status_code == 413


def test_llm_outage_is_reported_as_an_sse_error_event_and_nothing_is_saved(down_provider):
    app.dependency_overrides[get_gateway] = lambda: LLMGateway([down_provider])
    client = TestClient(app)
    sid = _screening(client)
    resp = _post(client, sid, "cv.txt", "\n".join(CV_LINES_EN).encode())
    assert resp.status_code == 200  # headers already sent; the error travels in-stream
    events = _parse_sse(resp.text)
    assert events[-1][0] == "error" and "unavailable" in events[-1][1]["detail"]
    assert client.get(f"/screenings/{sid}").json()["results"] == []
