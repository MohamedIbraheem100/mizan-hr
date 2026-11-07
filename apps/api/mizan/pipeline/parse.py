"""Parse node: file bytes -> numbered lines L1..Ln. CODE only, no LLM.

Line ids are the anchor for the whole pipeline: Judge cites them, Verify checks
quotes against them, the UI highlights them. They must be stable and dense.

Scanned PDFs (no text layer) are flagged, not processed here; LLM vision for
them is wired in M4.
"""

import re
from dataclasses import dataclass, field
from io import BytesIO
from typing import Literal

from docx import Document
from pypdf import PdfReader

SourceKind = Literal["pdf", "docx", "text"]

MAX_LINES = 600  # a CV is 1-3 pages; anything beyond this is noise or abuse
_WS = re.compile(r"[ \t ]+")
_BULLET = re.compile(r"^[•●▪–\-\*·]+\s*")


class UnsupportedFileError(ValueError):
    pass


@dataclass
class Line:
    id: str
    text: str


@dataclass
class ParsedCV:
    source: SourceKind
    lines: list[Line] = field(default_factory=list)
    page_count: int = 1
    has_text_layer: bool = True

    @property
    def text(self) -> str:
        return "\n".join(f"{line.id}: {line.text}" for line in self.lines)

    def line_map(self) -> dict[str, str]:
        return {line.id: line.text for line in self.lines}


def _clean(raw: str) -> str:
    raw = raw.replace("\r", "").strip()
    raw = _BULLET.sub("", raw)
    return _WS.sub(" ", raw).strip()


def _number(raw_lines: list[str]) -> list[Line]:
    lines: list[Line] = []
    for raw in raw_lines:
        text = _clean(raw)
        if not text:
            continue
        lines.append(Line(id=f"L{len(lines) + 1}", text=text))
        if len(lines) >= MAX_LINES:
            break
    return lines


def parse_pdf(data: bytes) -> ParsedCV:
    reader = PdfReader(BytesIO(data))
    raw_lines: list[str] = []
    for page in reader.pages:
        raw_lines.extend((page.extract_text() or "").splitlines())
    lines = _number(raw_lines)
    # Heuristic: a real text layer yields at least a handful of words.
    word_count = sum(len(line.text.split()) for line in lines)
    return ParsedCV(
        source="pdf",
        lines=lines,
        page_count=len(reader.pages),
        has_text_layer=word_count >= 15,
    )


def parse_docx(data: bytes) -> ParsedCV:
    doc = Document(BytesIO(data))
    raw_lines: list[str] = [p.text for p in doc.paragraphs]
    for table in doc.tables:  # skills/experience are often laid out in tables
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells]
            raw_lines.append(" | ".join(c for c in cells if c))
    return ParsedCV(source="docx", lines=_number(raw_lines))


def parse_text(text: str) -> ParsedCV:
    return ParsedCV(source="text", lines=_number(text.splitlines()))


def parse_file(filename: str, data: bytes) -> ParsedCV:
    """Dispatch on extension. Content sniffing (magic bytes) is added with upload limits in M4."""
    name = filename.lower()
    if name.endswith(".pdf"):
        return parse_pdf(data)
    if name.endswith(".docx"):
        return parse_docx(data)
    if name.endswith(".txt"):
        return parse_text(data.decode("utf-8", errors="replace"))
    raise UnsupportedFileError(f"unsupported file type: {filename!r} (use .pdf, .docx or .txt)")
