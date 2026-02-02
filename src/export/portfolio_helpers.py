# src/export/portfolio_helpers.py
from __future__ import annotations

from typing import Any, List, Dict

from .shared_helpers import (
    parse_date,
    format_date_range,
    strip_percent_tokens,
    clean_languages_above_threshold,
)

from src.insights.portfolio import format_skills_block, format_languages, format_frameworks

# Portfolio-only helpers

def reformat_duration_line(duration_line: str) -> str:
    """
    Input often like:
      "Duration: 2025-07-09 – 2025-10-31"
      "Duration: 2025-07-09 - 2025-10-31"
      "Duration: 2025-07-09 to 2025-10-31"
    Output:
      "Jul 2025 – Oct 2025"
    """
    s = (duration_line or "").strip()
    if not s:
        return ""

    # strip leading "Duration:"
    if s.lower().startswith("duration:"):
        s = s.split(":", 1)[1].strip()

    # normalize separators
    s = s.replace("—", "–")
    s = s.replace(" to ", " – ")
    s = s.replace(" - ", " – ")

    parts = [p.strip() for p in s.split("–")]
    if len(parts) == 2:
        start, end = parts[0], parts[1]
        return format_date_range(start, end)

    # single date fallback
    d = parse_date(s)
    return d.strftime("%b %Y") if d else ""

def _skills_one_line(summary: Dict[str, Any]) -> str:
    lines = format_skills_block(summary) or []
    if not lines:
        return ""
    if len(lines) == 1 and "N/A" in (lines[0] or ""):
        return ""

    out: List[str] = []
    for line in lines:
        t = (line or "").strip()
        if not t:
            continue
        # skip "Skills:" header if present
        if t.lower().startswith("skills"):
            continue
        if t.startswith(("-", "•")):
            t = t.lstrip("-•").strip()
        if t:
            out.append(t)
    return ", ".join(out)

def _languages_clean(summary: Dict[str, Any], *, min_pct: int = 10) -> str:
    # Prefer raw list with percents -> threshold + remove percent
    langs = clean_languages_above_threshold(summary.get("languages"), min_pct=min_pct)
    if langs:
        return ", ".join(langs)

    # Fallback: formatted string -> strip percent tokens
    s = strip_percent_tokens(format_languages(summary) or "")
    if s.lower().startswith("languages:"):
        s = s.split(":", 1)[1].strip()
    return s.strip() or "N/A"

def _frameworks_clean(summary: Dict[str, Any]) -> str:
    s = strip_percent_tokens(format_frameworks(summary) or "")
    if s.lower().startswith("frameworks:"):
        s = s.split(":", 1)[1].strip()
    return s.strip() or "N/A"

__all__ = [
    # re-export shared helpers
    "parse_date",
    "format_date_range",
    "strip_percent_tokens",
    "clean_languages_above_threshold",
    # portfolio-only
    "reformat_duration_line",
    "_skills_one_line",
    "_languages_clean",
    "_frameworks_clean"
]
