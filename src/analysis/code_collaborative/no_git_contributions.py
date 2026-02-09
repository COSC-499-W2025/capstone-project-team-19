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

from src.db import (
    get_files_for_project,
    get_files_for_version,
    store_file_contributions,
    get_zip_name_for_project,
)
from .code_collaborative_analysis_helper import rank_files_by_description


def _zip_base_dir(conn: sqlite3.Connection, user_id: int, project_name: str) -> str | None:
    """
    Resolve the base directory for extracted files: src/analysis/zip_data/<zip_name>.
    """
    zip_name = get_zip_name_for_project(conn, user_id, project_name)

    if not zip_name:
        return None

    # __file__ is src/analysis/code_collaborative/no_git_contributions.py
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    return os.path.join(src_dir, "analysis", "zip_data", zip_name)


def store_contributions_without_git(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    desc: str | None,
    debug: bool = False,
    version_key: int | None = None,
) -> None:
    """
    Main entry for no-git collaborative code:
      1) Pull code files for this user/project from DB.
      2) Score files against the user's description (names/paths + content slice).
      3) If no hits, fall back to “all code files”.
      4) Persist to user_code_contributions so activity/skills filters work.
    """
    if version_key is not None:
        files = get_files_for_version(conn, user_id, version_key, only_text=False)
    else:
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

    # Note: we store nominal counts (lines_changed=1) because we don't have git stats.
    # These values are only used for ordering/filtering in get_user_contributed_files and aren't used in the analysis in any way.
    contributions_dict = {
        path: {"lines_changed": 1, "commits_count": 0}
        for path in inferred
    }
    store_file_contributions(conn, user_id, project_name, contributions_dict)
