from mizan.pipeline.redact import REDACTED, REDACTED_LINE, apply_llm_redactions, regex_redact
from mizan.schemas.screening import RedactDraft


def test_regex_redacts_contacts_and_labelled_personal_fields():
    lines = {
        "L1": "Ahmed Hassan",
        "L2": "ahmed.hassan@example.com | +20 100 123 4567 | linkedin.com/in/ahmed",
        "L3": "Date of Birth: 12/03/1994",
        "L4": "Nationality: Egyptian | Married",
        "L5": "Senior Python Developer with 5 years of experience",
    }
    out, hits = regex_redact(lines)
    assert list(out) == list(lines)  # ids and order untouched
    assert "example.com" not in out["L2"] and "123" not in out["L2"] and "linkedin" not in out["L2"]
    assert out["L3"] == REDACTED_LINE and out["L4"] == REDACTED_LINE
    assert out["L5"] == lines["L5"]  # professional content untouched
    assert hits >= 5


def test_regex_redacts_arabic_personal_fields_and_words():
    lines = {
        "L1": "تاريخ الميلاد: 1994/3/12",
        "L2": "الحالة الاجتماعية: متزوج",
        "L3": "الجنسية: مصري",
        "L4": "مطور بايثون أول بخبرة 5 سنوات",
        "L5": "مهندس مصري يعمل في القاهرة",
    }
    out, _ = regex_redact(lines)
    assert out["L1"] == REDACTED_LINE and out["L2"] == REDACTED_LINE and out["L3"] == REDACTED_LINE
    assert out["L4"] == lines["L4"]
    assert "مصري" not in out["L5"] and "القاهرة" in out["L5"]


def test_llm_names_are_replaced_including_single_tokens():
    lines = {"L1": "Ahmed Hassan", "L5": "Ahmed led the migration; contact hassan for refs"}
    out, hits = apply_llm_redactions(lines, RedactDraft(person_names=["Ahmed Hassan"]))
    assert out["L1"] == REDACTED
    assert "Ahmed" not in out["L5"] and "hassan" not in out["L5"]
    assert hits == 3


def test_empty_llm_draft_changes_nothing():
    lines = {"L1": "text"}
    out, hits = apply_llm_redactions(lines, RedactDraft())
    assert out == lines and hits == 0
