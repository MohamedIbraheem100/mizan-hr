"""Redact node (Blind mode): remove identity and protected attributes BEFORE any
judgement happens. Regex handles the structured stuff; the LLM only lists names
and free-text identifiers, and CODE does the replacement. Line ids never change.
"""

import re

from mizan.schemas.screening import RedactDraft

REDACTED = "[REDACTED]"
REDACTED_LINE = "[REDACTED: personal data]"

# Inline patterns: replaced wherever they occur.
_INLINE = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),  # email
    re.compile(r"(?:https?://|www\.)\S+|linkedin\.com/\S+|github\.com/\S+", re.I),  # urls
    re.compile(r"(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)"),  # phone numbers (intl + local)
]

# Whole-line patterns: a labelled personal-data field -> the entire line is replaced.
_LINE_LABELS = re.compile(
    r"^\W*("
    r"date of birth|d\.?o\.?b\.?|birth ?date|born|age|gender|sex|nationality|citizenship|"
    r"religion|marital status|married|single|divorced|widowed|military (?:status|service)|"
    r"national id|passport|id number|photo|"
    r"تاريخ الميلاد|الميلاد|مواليد|العمر|السن|النوع|الجنس|الجنسية|الديانة|الدين|"
    r"الحالة الاجتماعية|الحالة الإجتماعية|متزوج|متزوجة|أعزب|اعزب|عزباء|مطلق|مطلقة|أرمل|"
    r"الموقف من التجنيد|موقف التجنيد|الخدمة العسكرية|الرقم القومي|رقم الهوية|جواز السفر|"
    r"صورة شخصية|الصورة"
    r")\b",
    re.I,
)
# Standalone protected words inside otherwise useful lines.
_INLINE_WORDS = re.compile(
    r"\b(male|female|muslim|christian|jewish|hindu|buddhist|married|single|divorced|widowed|"
    r"egyptian|saudi|emirati|jordanian|syrian|lebanese|sudanese|palestinian|"
    r"مسلم|مسلمة|مسيحي|مسيحية|ذكر|أنثى|انثى|متزوج|متزوجة|أعزب|عزباء|"
    r"مصري|مصرية|سعودي|سعودية|إماراتي|أردني|سوري|لبناني|سوداني|فلسطيني)\b",
    re.I,
)


def regex_redact(lines: dict[str, str]) -> tuple[dict[str, str], int]:
    out: dict[str, str] = {}
    hits = 0
    for line_id, text in lines.items():
        if _LINE_LABELS.search(text):
            out[line_id] = REDACTED_LINE
            hits += 1
            continue
        new = text
        for pat in _INLINE:
            new, n = pat.subn(REDACTED, new)
            hits += n
        new, n = _INLINE_WORDS.subn(REDACTED, new)
        hits += n
        out[line_id] = new
    return out, hits


def apply_llm_redactions(lines: dict[str, str], draft: RedactDraft) -> tuple[dict[str, str], int]:
    """Replace every string the model listed (and each name token of length > 2)."""
    terms: set[str] = set()
    for name in draft.person_names:
        name = name.strip()
        if len(name) > 1:
            terms.add(name)
            terms.update(tok for tok in re.split(r"\s+", name) if len(tok) > 2)
    terms.update(t.strip() for t in draft.other_identifiers if len(t.strip()) > 1)
    if not terms:
        return dict(lines), 0
    # Longest first so "Ahmed Hassan" is replaced before "Ahmed".
    pattern = re.compile("|".join(re.escape(t) for t in sorted(terms, key=len, reverse=True)), re.I)
    out: dict[str, str] = {}
    hits = 0
    for line_id, text in lines.items():
        new, n = pattern.subn(REDACTED, text)
        out[line_id] = new
        hits += n
    return out, hits


def numbered(lines: dict[str, str]) -> str:
    return "\n".join(f"{line_id}: {text}" for line_id, text in lines.items())
