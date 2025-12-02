from __future__ import annotations

"""
Helpers for collaborative code projects that lack a local .git directory.

Goal: infer which files the user likely worked on using their manual contribution
description plus lightweight keyword matching on file names, paths, and a small
slice of file content. This populates user_code_contributions so skills/activity
filters don't go empty in no-git scenarios.
"""

import os
import sqlite3
from typing import Iterable

from src.db import get_files_for_project, store_file_contributions
from .code_collaborative_analysis_helper import _top_keywords_from_descriptions


def _zip_base_dir(conn: sqlite3.Connection, user_id: int, project_name: str) -> str | None:
    """
    Resolve the base directory for extracted files: src/analysis/zip_data/<zip_name>.
    """
    try:
        cur = conn.execute(
            "SELECT zip_name FROM project_classifications WHERE user_id = ? AND project_name = ? LIMIT 1",
            (user_id, project_name),
        )
        row = cur.fetchone()
        zip_name = row[0] if row else None
    except Exception:
        zip_name = None

    if not zip_name:
        return None

    # __file__ is src/analysis/code_collaborative/no_git_contributions.py
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(src_dir, "analysis", "zip_data", zip_name)


def _read_content_slice(path: str, limit: int = 10000) -> str | None:
    """
    Read only the first `limit` bytes (~first 10KB of text) to keep I/O cheap.
    Enough to catch key identifiers and comments without loading entire files.
    """
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except Exception:
        return None


def rank_files_by_description(
    desc: str,
    files: Iterable[dict],
    base_dir: str | None = None,
    top_n: int = 8,
) -> list[str]:
    """
    Heuristic scorer:
      - Extract keywords from the user's non-LLM contribution description.
      - For each code file, score:
          * +2 per keyword found in basename (strong signal)
          * +1 per keyword found in path
          * +1 per keyword found in the first ~10KB of content (if base_dir provided)
      - Return the top-N file_paths with highest scores.

    Notes:
      - Content scan is bounded to avoid heavy reads.
      - If no keywords or no hits, the caller will fall back to “all files”.
    """
    files = list(files)
    if not files:
        return []

    desc = (desc or "").strip()
    keywords = _top_keywords_from_descriptions([desc], k=top_n) if desc else []
    keyword_set = [k.lower() for k in keywords if k]

    scores: list[tuple[int, str]] = []
    for row in files:
        rel_path = row.get("file_path") or ""
        fp = rel_path.lower()
        bn = (row.get("file_name") or "").lower()
        if not fp:
            continue

        content_hits = 0
        if base_dir:
            abs_path = os.path.join(base_dir, rel_path)
            content = _read_content_slice(abs_path)
            if content:
                content_lower = content.lower()
                for kw in keyword_set:
                    if kw and kw in content_lower:
                        content_hits += 1

        # Score blend: basename hit (+2), path hit (+1), content keyword hit (+1)
        score = 0
        for kw in keyword_set:
            if kw in bn:
                score += 2  # basename hit is stronger
            if kw in fp:
                score += 1
        score += content_hits

        if score > 0:
            scores.append((score, rel_path))

    scores.sort(key=lambda t: (-t[0], t[1]))
    ranked = [fp for _score, fp in scores[:top_n] if fp]
    return ranked


def store_contributions_without_git(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    desc: str | None,
    debug: bool = False,
) -> None:
    """
    Main entry for no-git collaborative code:
      1) Pull code files for this user/project from DB.
      2) Score files against the user's description (names/paths + content slice).
      3) If no hits, fall back to “all code files”.
      4) Persist to user_code_contributions so activity/skills filters work.
    """
    files = get_files_for_project(conn, user_id, project_name, only_text=False)
    code_files = [f for f in files if f.get("file_type") == "code" and f.get("file_path")]
    if not code_files:
        return

    base_dir = _zip_base_dir(conn, user_id, project_name)
    inferred = rank_files_by_description(desc or "", code_files, base_dir=base_dir, top_n=8) # Top 8 files (can adjust if needed)

    if not inferred:
        inferred = [f["file_path"] for f in code_files if f.get("file_path")]

    if not inferred:
        return

    if debug:
        print("[debug] inferred contributions (no git):")
        for path in inferred:
            print(f"  - {path}")

    contributions_dict = {
        path: {"lines_changed": 1, "commits_count": 0}
        for path in inferred
    }
    store_file_contributions(conn, user_id, project_name, contributions_dict)
