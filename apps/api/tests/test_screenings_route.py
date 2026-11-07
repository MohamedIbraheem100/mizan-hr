from datetime import timedelta

from fastapi.testclient import TestClient

from mizan.db import repo
from mizan.db.models import ScreeningRow, utcnow
from mizan.db.session import get_sessionmaker
from mizan.main import app
from tests.pipeline_fixtures import RUBRIC

client = TestClient(app)


def test_create_then_get_screening_round_trip():
    created = client.post("/screenings", json={"rubric": RUBRIC, "blind": False})
    assert created.status_code == 201, created.text
    body = created.json()
    sid = body["screening_id"]
    assert body["blind"] is False and body["expires_at"]

    got = client.get(f"/screenings/{sid}")
    assert got.status_code == 200
    view = got.json()
    assert view["rubric"]["job_title"] == "Backend Engineer"
    assert [c["id"] for c in view["rubric"]["criteria"]] == ["c1", "c2", "c3"]
    assert view["results"] == []


def test_blind_defaults_to_true():
    created = client.post("/screenings", json={"rubric": RUBRIC})
    assert created.json()["blind"] is True


def test_invalid_rubric_is_422():
    bad = dict(RUBRIC, criteria=[dict(RUBRIC["criteria"][2])])  # nice_to_have only
    assert client.post("/screenings", json={"rubric": bad}).status_code == 422


def test_unknown_screening_is_404():
    assert client.get("/screenings/does-not-exist").status_code == 404


def test_expired_screening_is_410():
    sid = client.post("/screenings", json={"rubric": RUBRIC}).json()["screening_id"]
    with get_sessionmaker()() as db:
        row = db.get(ScreeningRow, sid)
        row.expires_at = utcnow() - timedelta(minutes=1)
        db.commit()
    assert client.get(f"/screenings/{sid}").status_code == 410


def test_rubric_is_persisted_as_confirmed_not_as_proposed():
    """The recruiter's edited weights are what gets stored and used."""
    edited = dict(RUBRIC)
    edited["criteria"] = [dict(c) for c in RUBRIC["criteria"]]
    edited["criteria"][0]["weight"] = 0.8
    sid = client.post("/screenings", json={"rubric": edited}).json()["screening_id"]
    with get_sessionmaker()() as db:
        rubric = repo.rubric_of(repo.get_screening(db, sid))
    assert rubric.criteria[0].weight > 0.6  # normalized 0.8 / (0.8+0.3+0.2)
