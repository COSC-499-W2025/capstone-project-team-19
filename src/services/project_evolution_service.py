"""Business logic for project version evolution."""

from sqlite3 import Connection
from typing import Any, Dict, List, Optional

from src.db.version_evolution import (
    get_version_keys_ordered_for_project,
    get_version_summary,
    get_version_skills,
    get_file_diff_between_versions,
    get_skill_diff_between_versions,
)


def _compute_loc_delta(
    prev_added: Optional[int],
    prev_deleted: Optional[int],
    curr_added: Optional[int],
    curr_deleted: Optional[int],
) -> Optional[Dict[str, Optional[int]]]:
    """Compute LOC delta between consecutive version snapshots."""
    diff_added = None
    diff_removed = None

    if curr_added is not None:
        diff_added = (curr_added - prev_added) if prev_added is not None else curr_added
    if curr_deleted is not None:
        diff_removed = (curr_deleted - prev_deleted) if prev_deleted is not None else curr_deleted

    if diff_added is None and diff_removed is None:
        return None
    return {"linesAdded": diff_added, "linesModified": None, "linesRemoved": diff_removed}


def get_evolution_for_project(conn: Connection, project_key: int) -> List[Dict[str, Any]]:
    """
    Return all versions for a project with summary, skills, file-level diffs,
    skill progression, and enriched metrics.  Ordered oldest first.
    """
    versions_rows = get_version_keys_ordered_for_project(conn, project_key)
    if not versions_rows:
        return []

    result: List[Dict[str, Any]] = []
    prev_version_key: Optional[int] = None
    prev_lines_added: Optional[int] = None
    prev_lines_deleted: Optional[int] = None

    for version_key, created_at in versions_rows:
        vs = get_version_summary(conn, version_key)
        skills = get_version_skills(conn, version_key)

        lines_added = vs["lines_added"] if vs else None
        lines_deleted = vs["lines_deleted"] if vs else None

        loc_diff = _compute_loc_delta(prev_lines_added, prev_lines_deleted, lines_added, lines_deleted)

        file_diff = None
        skill_progression = None
        if prev_version_key is not None:
            file_diff = get_file_diff_between_versions(conn, prev_version_key, version_key)
            skill_progression = get_skill_diff_between_versions(conn, prev_version_key, version_key)

        diff_dict = None
        if loc_diff or file_diff:
            diff_dict = loc_diff or {"linesAdded": None, "linesModified": None, "linesRemoved": None}
            if file_diff:
                diff_dict["files"] = {
                    "filesAdded": file_diff["added"],
                    "filesModified": file_diff["modified"],
                    "filesRemoved": file_diff["removed"],
                    "unchangedCount": file_diff["unchanged_count"],
                }

        prev_version_key = version_key
        prev_lines_added = lines_added
        prev_lines_deleted = lines_deleted

        raw_date = (vs["activity_date"] if vs and vs.get("activity_date") else created_at) or created_at
        date_str = raw_date[:10] if raw_date and len(raw_date) >= 10 else raw_date or ""

        entry: Dict[str, Any] = {
            "versionId": str(version_key),
            "date": date_str,
            "summary": (vs["summary_text"] if vs else None) or "",
            "diff": diff_dict,
            "skills": [s["skill_name"] for s in skills],
            "skillsDetail": skills,
            "skillProgression": skill_progression,
            "languages": vs.get("languages", []) if vs else [],
            "frameworks": vs.get("frameworks", []) if vs else [],
            "avgComplexity": vs.get("avg_complexity") if vs else None,
            "totalFiles": vs.get("total_files") if vs else None,
        }
        result.append(entry)

    return result
