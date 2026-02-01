# src/export/portfolio_helpers.py
from __future__ import annotations

from typing import Any, List

from .shared_helpers import (
    parse_date,
    format_date_range,
    strip_percent_tokens,
    clean_languages_above_threshold,
)

# -------------------------
# Portfolio-only helpers
# -------------------------

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


__all__ = [
    # re-export shared helpers (optional convenience)
    "parse_date",
    "format_date_range",
    "strip_percent_tokens",
    "clean_languages_above_threshold",
    # portfolio-only
    "reformat_duration_line",
]
