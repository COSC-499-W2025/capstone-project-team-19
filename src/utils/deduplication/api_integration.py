from __future__ import annotations

import os
import sqlite3
from typing import Any, Dict, Set, Optional

from src.utils.deduplication.register_project import register_project
from src.utils.deduplication.fingerprints import project_fingerprints

from src.db import (
    insert_project,
    insert_project_version,
    insert_version_files,
    _lookup_existing_name
)


def find_project_dir(target_dir: str, root_name: str | None, project_name: str) -> str | None:
    """
    Reuses the CLI's "candidate directories" logic so we can locate a project's extracted folder reliably.
    """
    base_path = os.path.join(target_dir, root_name) if root_name else target_dir

    candidates = [
        os.path.join(base_path, project_name),
        os.path.join(target_dir, project_name),
    ]

    if root_name:
        candidates.insert(0, os.path.join(target_dir, root_name, project_name))
        candidates.insert(0, os.path.join(target_dir, root_name, "individual", project_name))
        candidates.insert(0, os.path.join(target_dir, root_name, "collaborative", project_name))

    for cand in candidates:
        if os.path.isdir(cand):
            return cand
    return None


def force_register_new_project(
    conn: sqlite3.Connection,
    user_id: int,
    display_name: str,
    project_dir: str,
    upload_id: int | None = None,
) -> dict[str, Any]:
    """
    Always creates a NEW project + version (even if similar to another project).
    Useful when user chooses "new_project" for an 'ask' case.
    """
    fp_strict, fp_loose, entries = project_fingerprints(project_dir)
    with conn:
        pk = insert_project(conn, user_id, display_name)
        vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
        insert_version_files(conn, vk, entries)
    return {"project_key": pk, "version_key": vk}


def force_register_new_version(
    conn: sqlite3.Connection,
    project_key: int,
    project_dir: str,
    upload_id: int | None = None,
) -> dict[str, Any]:
    """
    Always creates a NEW version under an existing project_key.
    Note: if it's an exact strict-duplicate of an existing version for this project_key,
    your UNIQUE(project_key, fingerprint_strict) constraint will block it (which is fine).
    """
    fp_strict, fp_loose, entries = project_fingerprints(project_dir)
    with conn:
        vk = insert_project_version(conn, project_key, upload_id, fp_strict, fp_loose)
        insert_version_files(conn, vk, entries)
    return {"project_key": project_key, "version_key": vk}


def run_deduplication_for_projects_api(
    conn: sqlite3.Connection,
    user_id: int,
    target_dir: str,
    layout: dict,
    upload_id: int | None = None,
) -> dict[str, Any]:
    """
    API-safe version of CLI dedup:
    - 'duplicate' -> skip automatically
    - 'new_version' -> record suggestion (and register_project already inserts the version)
    - 'ask' -> record ask info for UI (no prompting)
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
        project_dir = find_project_dir(target_dir, root_name, project_name)
        if not project_dir:
            continue

        result = register_project(conn, user_id, project_name, project_dir, upload_id=upload_id)
        kind = result.get("kind")

        if kind == "duplicate":
            skipped.add(project_name)

        elif kind == "new_version":
            pk = result.get("project_key")
            existing = _lookup_existing_name(conn, int(pk)) if pk is not None else None
            if existing:
                new_versions[project_name] = existing

        elif kind == "ask":
            best_pk = result.get("best_match_project_key")
            existing = _lookup_existing_name(conn, int(best_pk)) if best_pk is not None else None
            asks[project_name] = {
                "existing": existing,
                "best_match_project_key": best_pk,   # IMPORTANT: resolve endpoint needs this
                "similarity": result.get("similarity"),
                "file_count": result.get("file_count"),
            }

    return {"skipped": skipped, "asks": asks, "new_versions": new_versions}


