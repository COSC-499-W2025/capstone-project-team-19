# src/export/shared_helpers.py
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional

# -------------------------
# Date helpers (shared)
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


# -------------------------
# Percent stripping (shared)
# -------------------------

_PCT_TOKEN_RE = re.compile(r"\s*\b\d+(\.\d+)?\s*%\b")

def strip_percent_tokens(text: str) -> str:
    """
    "Final 100%" -> "Final"
    "Python 88%" -> "Python"
    """
    t = (text or "").strip()
    if not t:
        return ""
    t = _PCT_TOKEN_RE.sub("", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


# -------------------------
# Language threshold cleaner (shared)
# -------------------------

_LANG_PCT_RE = re.compile(r"^\s*(?P<name>.+?)\s+(?P<pct>\d+)\s*%\s*$")

def clean_languages_above_threshold(values: Any, *, min_pct: int = 10) -> List[str]:
    """
    Input:
      ["Python 88%", "CSS 10%", "JSON 5%"]
    Output (min_pct=10):
      ["Python", "CSS"]  # keeps pct >= min_pct
    Rules:
      - keeps pct >= min_pct
      - dedupes by taking max pct per language
      - ignores malformed entries
      - sorts by pct desc, then name asc (stable)
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
        try:
            pct = int(m.group("pct"))
        except ValueError:
            continue

        if pct < min_pct:
            continue

        prev = best.get(name)
        if prev is None or pct > prev:
            best[name] = pct

    return [name for name, _pct in sorted(best.items(), key=lambda kv: (-kv[1], kv[0].lower()))]


__all__ = [
    "parse_date",
    "format_date_range",
    "strip_percent_tokens",
    "clean_languages_above_threshold",
]
