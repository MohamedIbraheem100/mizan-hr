from io import BytesIO

import pytest
from docx import Document

from mizan.pipeline.parse import UnsupportedFileError, parse_file

EN_LINES = [
    "Ahmed Hassan",
    "Senior Python Developer",
    "• 5 years of experience with FastAPI and PostgreSQL",
    "Led a team of 4 engineers (2021-2025)",
]
AR_LINES = [
    "أحمد حسن",
    "مطور بايثون أول",
    "خبرة 5 سنوات في FastAPI و PostgreSQL",
    "قيادة فريق من 4 مهندسين",
]


def _docx(lines: list[str], table: list[list[str]] | None = None) -> bytes:
    doc = Document()
    for line in lines:
        doc.add_paragraph(line)
    if table:
        t = doc.add_table(rows=0, cols=len(table[0]))
        for row in table:
            cells = t.add_row().cells
            for cell, value in zip(cells, row, strict=True):
                cell.text = value
    buf = BytesIO()
    doc.save(buf)
    return buf.getvalue()


def _pdf(lines: list[str]) -> bytes:
    """Minimal single-page PDF with a real text layer (ASCII only, Helvetica)."""
    content = (
        "BT /F1 12 Tf 72 720 Td 14 TL "
        + " ".join(f"({line.replace('(', '[').replace(')', ']')}) Tj T*" for line in lines)
        + " ET"
    )
    objs = [
        "<< /Type /Catalog /Pages 2 0 R >>",
        "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        "/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
        "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        f"<< /Length {len(content)} >>\nstream\n{content}\nendstream",
    ]
    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(out.tell())
        out.write(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1"))
    xref = out.tell()
    out.write(f"xref\n0 {len(objs) + 1}\n0000000000 65535 f \n".encode())
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode())
    out.write(
        f"trailer\n<< /Size {len(objs) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode()
    )
    return out.getvalue()


def test_docx_english_lines_are_numbered_and_cleaned():
    cv = parse_file("cv.docx", _docx(EN_LINES))
    assert cv.source == "docx"
    assert [line.id for line in cv.lines] == ["L1", "L2", "L3", "L4"]
    assert cv.lines[2].text.startswith("5 years")  # bullet stripped
    assert cv.line_map()["L4"] == "Led a team of 4 engineers (2021-2025)"


def test_docx_arabic_is_preserved():
    cv = parse_file("cv.docx", _docx(AR_LINES))
    assert cv.lines[0].text == "أحمد حسن"
    assert "FastAPI" in cv.lines[2].text


def test_docx_tables_are_flattened_into_lines():
    cv = parse_file("cv.docx", _docx(["Skills"], table=[["Python", "Expert"], ["SQL", "Good"]]))
    texts = [line.text for line in cv.lines]
    assert "Python | Expert" in texts and "SQL | Good" in texts


def test_pdf_with_text_layer():
    cv = parse_file("cv.pdf", _pdf([line for line in EN_LINES if line.isascii()] * 4))
    assert cv.source == "pdf"
    assert cv.page_count == 1
    assert cv.has_text_layer is True
    assert cv.lines[0].text == "Ahmed Hassan"


def test_pdf_without_text_is_flagged_as_scanned():
    cv = parse_file("scan.pdf", _pdf([]))
    assert cv.has_text_layer is False
    assert cv.lines == []


def test_text_file_and_blank_lines():
    cv = parse_file("cv.txt", b"Line one\n\n\n   Line   two  \n")
    assert [line.text for line in cv.lines] == ["Line one", "Line two"]
    assert cv.text == "L1: Line one\nL2: Line two"


def test_unsupported_extension():
    with pytest.raises(UnsupportedFileError):
        parse_file("cv.exe", b"MZ")
