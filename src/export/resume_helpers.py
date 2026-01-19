from __future__ import annotations

from datetime import datetime
from typing import Any, Optional, List, Dict

from docx import Document
import re

# -------------------------
# Date helpers
# -------------------------

def parse_date(value: Any) -> Optional[datetime]:
    """
    Best-effort parse for common DB / snapshot date strings.
    Supports:
      - YYYY-MM-DD
      - YYYY-MM-DD HH:MM:SS
      - YYYY-MM-DDTHH:MM:SS
    """
    if not isinstance(value, str):
        return None
    s = value.strip()
    if not s:
        return None

    candidates = [s, s[:19]]
    fmts = ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S")
    for c in candidates:
        for fmt in fmts:
            try:
                return datetime.strptime(c, fmt)
            except ValueError:
                continue
    return None


def format_date_range(start: Any, end: Any) -> str:
    """
    Output examples:
      - 'Nov 2024 – Dec 2024'
      - 'Sep 2024 – Present'
      - '' if no dates
    """
    ds = parse_date(start)
    de = parse_date(end)

    def fmt(d: datetime) -> str:
        return d.strftime("%b %Y")

    if ds and de:
        return f"{fmt(ds)} – {fmt(de)}"
    if ds and not de:
        return f"{fmt(ds)} – Present"
    if not ds and de:
        return fmt(de)
    return ""

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

# -------------------------
# DOCX helpers
# -------------------------

def add_section_heading(doc: Document, title: str) -> None:
    doc.add_heading(title.upper(), level=1)


def add_placeholder(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text)
    if p.runs:
        p.runs[0].italic = True


def add_bullet(doc: Document, text: str) -> None:
    p = doc.add_paragraph(text, style="List Bullet")
    p.paragraph_format.space_after = 0


# Clean language in skills section

_LANG_PCT_RE = re.compile(r"^\s*(?P<name>.+?)\s+(?P<pct>\d+)\s*%\s*$")

def clean_languages_above_threshold(
    values: Any,
    *,
    min_pct: int = 10,
) -> List[str]:
    """
    Input example:
      ["Python 88%", "JavaScript 54%", "CSS 10%", "JSON 5%", "JSON 6%"]
    Output (min_pct=10, strict >):
      ["Python", "JavaScript"]  # (and other >10 items)
    Rules:
      - strips percentages entirely
      - keeps only pct > min_pct
      - dedupes by taking max pct per language
      - ignores malformed entries
    """
    if not isinstance(values, list):
        return []

    best: Dict[str, int] = {}

    for raw in values:
        s = str(raw).strip()
        if not s:
            continue

        m = _LANG_PCT_RE.match(s)
        if not m:
            continue

        name = m.group("name").strip()
        pct = int(m.group("pct"))

        if pct < min_pct:  # strict ">"
            continue

        prev = best.get(name)
        if prev is None or pct > prev:
            best[name] = pct

    # sort by pct desc, then name asc for stable output
    return [name for name, _pct in sorted(best.items(), key=lambda kv: (-kv[1], kv[0].lower()))]
