# src/export/resume_helpers.py
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from docx import Document

from .shared_helpers import (
    parse_date,
    format_date_range,
    strip_percent_tokens,
    clean_languages_above_threshold,
)

# -------------------------
# Resume-only helpers (DOCX)
# -------------------------

def add_role_date_line(doc: Document, role: str, date_line: str) -> None:
    """
    Renders: Role | Nov 2024 – Dec 2024
    If date_line is empty, still shows role (or placeholder).
    """
    role = (role or "").strip()
    date_line = (date_line or "").strip()

    if role and date_line:
        line = f"{role} | {date_line}"
    elif role:
        line = role
    elif date_line:
        line = date_line
    else:
        line = ""

    if line:
        p = doc.add_paragraph(line)
        if p.runs:
            p.runs[0].italic = True


def _project_sort_key(p: dict) -> datetime:
    """
    Sort by:
      1. end_date (preferred)
      2. start_date
      3. very old fallback (goes last)
    """
    end = parse_date(p.get("end_date"))
    start = parse_date(p.get("start_date"))

    if end:
        return end
    if start:
        return start

    # projects with no dates go last
    return datetime.min


def add_section_heading(doc: Document, title: str) -> None:
    doc.add_heading((title or "").upper(), level=1)


def add_placeholder(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    if p.runs:
        p.runs[0].italic = True


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.space_after = 0


__all__ = [
    # shared helpers
    "parse_date",
    "format_date_range",
    "strip_percent_tokens",
    "clean_languages_above_threshold",
    # resume helpers
    "add_role_date_line",
    "_project_sort_key",
    "add_section_heading",
    "add_placeholder",
    "add_bullet",
]
