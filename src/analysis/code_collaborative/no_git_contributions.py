from __future__ import annotations

import sqlite3
from typing import Iterable, List

from src.db import get_files_for_project, store_file_contributions
from .code_collaborative_analysis_helper import _top_keywords_from_descriptions


def rank_files_by_description(
    desc: str,
    files: Iterable[dict],
    top_n: int = 8,
) -> list[str]:
    """
    Infer likely contributed files by matching keywords from a description
    against basenames/paths. Returns a list of file_path strings.
    """
    files = list(files)
    if not files:
        return []

    desc = (desc or "").strip()
    keywords = _top_keywords_from_descriptions([desc], k=top_n) if desc else []
    keyword_set = [k.lower() for k in keywords if k]

    scores: list[tuple[int, str]] = []
    for row in files:
        fp = (row.get("file_path") or "").lower()
        bn = (row.get("file_name") or "").lower()
        if not fp:
            continue

        score = 0
        for kw in keyword_set:
            if kw in bn:
                score += 2  # basename hit is stronger
            if kw in fp:
                score += 1

        if score > 0:
            scores.append((score, row.get("file_path") or ""))

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
    Infer contributed files (keyword match or fallback to all code files) and
    store them so activity/skills can filter correctly.
    """
    files = get_files_for_project(conn, user_id, project_name, only_text=False)
    code_files = [f for f in files if f.get("file_type") == "code" and f.get("file_path")]
    if not code_files:
        return

    inferred = rank_files_by_description(desc or "", code_files, top_n=8)

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
