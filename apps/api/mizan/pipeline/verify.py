"""Verify node: CODE, not LLM. The anti-hallucination gate.

Every quote the Judge cited must actually exist in the cited line (after
normalization, fuzzy ratio >= 0.9). Quotes that fail are dropped; a "met" or
"partial" verdict left with no surviving evidence becomes "no_evidence".
"""

import re
import unicodedata
from difflib import SequenceMatcher

from mizan.schemas.rubric import Rubric
from mizan.schemas.screening import CriterionJudgment, Evidence, JudgeDraft, VerifyStats

THRESHOLD = 0.9

_ARABIC_DIACRITICS = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)
_WS = re.compile(r"\s+")
_ARABIC_MAP = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
        "ى": "ي",
        "ئ": "ي",
        "ؤ": "و",
        "ة": "ه",
        "گ": "ك",
        "ک": "ك",
        "ی": "ي",
        "٠": "0",
        "١": "1",
        "٢": "2",
        "٣": "3",
        "٤": "4",
        "٥": "5",
        "٦": "6",
        "٧": "7",
        "٨": "8",
        "٩": "9",
    }
)


def normalize(text: str) -> str:
    """Case, width, diacritics, Arabic letter variants, punctuation, whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = _ARABIC_DIACRITICS.sub("", text)
    text = text.translate(_ARABIC_MAP).casefold()
    text = _NON_WORD.sub(" ", text)
    return _WS.sub(" ", text).strip()


def similarity(quote: str, line: str) -> float:
    """How much of the normalized quote is found, in order, inside the normalized line.

    1.0 when the quote is a literal substring. Otherwise the share of the quote's
    characters covered by in-order matching blocks, so a dropped word or a typo
    still scores high while a different sentence built from the same vocabulary
    (reordered words) scores low.
    """
    q, ln = normalize(quote), normalize(line)
    if not q or not ln:
        return 0.0
    if q in ln:
        return 1.0
    matcher = SequenceMatcher(None, q, ln, autojunk=False)
    covered = sum(block.size for block in matcher.get_matching_blocks())
    return covered / len(q)


def quote_matches(quote: str, line_id: str, line_map: dict[str, str]) -> bool:
    """The quote must be in the cited line.

    PDF extraction often wraps one sentence over two lines, so a quote may also
    span the cited line and a neighbour. The anchor stays the cited line: a quote
    that lives entirely in the neighbour is rejected (wrong line id).
    """
    line = line_map.get(line_id)
    if line is None:
        return False
    if similarity(quote, line) >= THRESHOLD:
        return True
    n = int(line_id[1:]) if line_id[1:].isdigit() else None
    if n is None:
        return False
    for neighbour_id in (f"L{n - 1}", f"L{n + 1}"):
        other = line_map.get(neighbour_id)
        if other is None or similarity(quote, other) >= THRESHOLD:
            continue  # missing, or the quote belongs to the neighbour alone
        joined = f"{other} {line}" if neighbour_id == f"L{n - 1}" else f"{line} {other}"
        if similarity(quote, joined) >= THRESHOLD:
            return True
    return False


def verify(
    draft: JudgeDraft, rubric: Rubric, line_map: dict[str, str]
) -> tuple[list[CriterionJudgment], VerifyStats]:
    stats = VerifyStats()
    by_id = {j.criterion_id: j for j in draft.judgments}
    out: list[CriterionJudgment] = []

    for criterion in rubric.criteria:  # the rubric, not the model, decides the list
        j = by_id.get(criterion.id)
        if j is None:  # model skipped a criterion: that is "no evidence", not "met"
            out.append(
                CriterionJudgment(
                    criterion_id=criterion.id,
                    criterion_name=criterion.name,
                    criterion_type=criterion.type,
                    weight=criterion.weight,
                    verdict="no_evidence",
                    reasoning="no judgment returned for this criterion",
                )
            )
            continue

        kept: list[Evidence] = []
        dropped: list[Evidence] = []
        for ev in j.evidence:
            stats.quotes_checked += 1
            if quote_matches(ev.quote, ev.line_id, line_map):
                kept.append(ev)
                stats.quotes_verified += 1
            else:
                dropped.append(ev)
                stats.quotes_dropped += 1

        verdict = j.verdict
        before = None
        if verdict in ("met", "partial") and not kept:
            before, verdict = verdict, "no_evidence"
            stats.verdicts_downgraded += 1

        out.append(
            CriterionJudgment(
                criterion_id=criterion.id,
                criterion_name=criterion.name,
                criterion_type=criterion.type,
                weight=criterion.weight,
                verdict=verdict,
                evidence=kept,
                dropped_evidence=dropped,
                reasoning=j.reasoning,
                verdict_before_verify=before,
            )
        )
    return out, stats
