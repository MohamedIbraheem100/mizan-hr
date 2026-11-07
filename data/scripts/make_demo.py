# ruff: noqa: E501
"""Precompute the public demo: the 10 synthetic CVs screened (Blind mode) against
the backend-engineer JD with the REAL pipeline, saved as one JSON the web app
serves from /demo even when every LLM API is down.

Run from apps/api (so `mizan` imports), with LLM keys in .env:

    python ../../data/scripts/make_demo.py

Writes apps/web/public/demo/backend-engineer.json
"""

import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "apps" / "api"))

from mizan.core.config import get_settings  # noqa: E402
from mizan.llm.gateway import LLMGateway, build_providers  # noqa: E402
from mizan.llm.prompts import RUBRIC_SYSTEM, rubric_user_prompt  # noqa: E402
from mizan.pipeline.graph import run_screening  # noqa: E402
from mizan.pipeline.parse import parse_file  # noqa: E402
from mizan.schemas.rubric import RubricDraft  # noqa: E402
from mizan.schemas.screening import ProgressEvent, ScreeningResult  # noqa: E402

CV_DIR = REPO / "data" / "sample_cvs"
JD = REPO / "data" / "sample_jds" / "backend_engineer_en.txt"
OUT = REPO / "apps" / "web" / "public" / "demo" / "backend-engineer.json"


def screen(gw, rubric, path: Path, ref: str) -> dict:
    cv = parse_file(path.name, path.read_bytes())
    lines = None
    result = None
    for item in run_screening(gw, rubric=rubric, cv=cv, blind=True, candidate_ref=ref):
        if isinstance(item, ProgressEvent) and item.node in ("parse", "redact"):
            lines = item.detail.get("lines", lines)
        elif isinstance(item, ScreeningResult):
            result = item
    return {"result": result.model_dump(mode="json"), "lines": lines, "fileName": path.name}


def main() -> None:
    s = get_settings()
    gw = LLMGateway(build_providers(s), timeout_s=s.llm_timeout_s)
    rubric = gw.complete_json(
        system=RUBRIC_SYSTEM, user=rubric_user_prompt(JD.read_text("utf-8")), schema=RubricDraft
    ).data.to_rubric()
    paths = sorted(CV_DIR.glob("*.docx"))
    started = time.perf_counter()
    with ThreadPoolExecutor(max_workers=3) as pool:
        items = list(
            pool.map(
                lambda ip: screen(gw, rubric, ip[1], f"Candidate {ip[0] + 1:02d}"), enumerate(paths)
            )
        )
    items.sort(key=lambda i: (i["result"]["must_haves_met"], i["result"]["score"]), reverse=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(
            {
                "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "jd_text": JD.read_text("utf-8"),
                "rubric": rubric.model_dump(mode="json"),
                "blind": True,
                "items": items,
            },
            ensure_ascii=False,
            indent=1,
        ),
        encoding="utf-8",
    )
    print(f"wrote {OUT} ({OUT.stat().st_size // 1024} KB) in {time.perf_counter() - started:.0f}s")
    for i in items:
        r = i["result"]
        print(
            f"  {r['candidate_ref']:<13} {r['score']:>3} must={r['must_haves_met']} dropped={r['verify']['quotes_dropped']}"
        )


if __name__ == "__main__":
    main()
