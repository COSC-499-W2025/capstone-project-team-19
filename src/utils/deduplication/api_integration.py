import os
import sqlite3
from typing import Dict, Set, Tuple, Any

from src.utils.deduplication.register_project import register_project


def _lookup_existing_name(conn: sqlite3.Connection, project_key: str) -> str | None:
    row = conn.execute(
        "SELECT display_name FROM projects WHERE project_key = ?",
        (project_key,),
    ).fetchone()
    return row[0] if row else None


def run_deduplication_for_projects_api(
    conn: sqlite3.Connection,
    user_id: int,
    target_dir: str,
    layout: dict,
) -> dict:
    """
    API-safe version of run_deduplication_for_projects:
    - skips exact duplicates automatically
    - does NOT prompt for "ask" cases (just records them in state so UI can handle later)
    - records "new_version" suggestions for later (no renaming in v1 unless you want it)
    """
    root_name = layout.get("root_name")
    all_projects = set(layout.get("auto_assignments", {}).keys())
    all_projects.update(layout.get("pending_projects", []))

    if not all_projects:
        return {"skipped": set(), "asks": {}, "new_versions": {}}

    base_path = os.path.join(target_dir, root_name) if root_name else target_dir

    skipped: Set[str] = set()
    asks: Dict[str, Any] = {}
    new_versions: Dict[str, str] = {}

    for project_name in all_projects:
        candidates = [
            os.path.join(base_path, project_name),
            os.path.join(target_dir, project_name),
        ]
        if root_name:
            candidates.insert(0, os.path.join(target_dir, root_name, project_name))
            candidates.insert(0, os.path.join(target_dir, root_name, "individual", project_name))
            candidates.insert(0, os.path.join(target_dir, root_name, "collaborative", project_name))

        project_dir = None
        for cand in candidates:
            if os.path.isdir(cand):
                project_dir = cand
                break
        if not project_dir:
            continue

        result = register_project(conn, user_id, project_name, project_dir)
        kind = result.get("kind")

        if kind == "duplicate":
            skipped.add(project_name)

        elif kind == "new_version":
            pk = result.get("project_key")
            existing = _lookup_existing_name(conn, pk) if pk else None
            if existing:
                new_versions[project_name] = existing

        elif kind == "ask":
            best_pk = result.get("best_match_project_key")
            existing = _lookup_existing_name(conn, best_pk) if best_pk else None
            asks[project_name] = {
                "existing": existing,
                "similarity": result.get("similarity"),
                "file_count": result.get("file_count"),
            }

    return {"skipped": skipped, "asks": asks, "new_versions": new_versions}
