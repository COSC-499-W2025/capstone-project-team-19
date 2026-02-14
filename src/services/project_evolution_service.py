"""Business logic for project version evolution."""

from sqlite3 import Connection
from typing import Any, Dict, List

from src.db.version_evolution import (
    get_version_keys_ordered_for_project,
    get_version_summary,
    get_version_skills,
)


def get_evolution_for_project(conn: Connection, project_key: int) -> List[Dict[str, Any]]:
    """
    Return all versions for a project with summary, skills, and computed diffs.
    Ordered oldest first.
    """
    versions_rows = get_version_keys_ordered_for_project(conn, project_key)
    if not versions_rows:
        return []

    result = []
    prev_lines_added = None
    prev_lines_deleted = None

    for version_key, created_at in versions_rows:
        vs = get_version_summary(conn, version_key)
        skills = get_version_skills(conn, version_key)

        lines_added = vs["lines_added"] if vs else None
        lines_deleted = vs["lines_deleted"] if vs else None

        diff_added = None
        diff_removed = None
        if prev_lines_added is not None and lines_added is not None:
            diff_added = lines_added - prev_lines_added
        if prev_lines_deleted is not None and lines_deleted is not None:
            diff_removed = lines_deleted - prev_lines_deleted
        if prev_lines_added is None and lines_added is not None:
            diff_added = lines_added
        if prev_lines_deleted is None and lines_deleted is not None:
            diff_removed = lines_deleted

        prev_lines_added = lines_added
        prev_lines_deleted = lines_deleted

        raw_date = (vs["activity_date"] if vs and vs.get("activity_date") else created_at) or created_at
        date_str = raw_date[:10] if raw_date and len(raw_date) >= 10 else raw_date or ""

        result.append({
            "versionId": str(version_key),
            "date": date_str,
            "summary": (vs["summary_text"] if vs else None) or "",
            "diff": (
                {"added": diff_added, "modified": None, "removed": diff_removed}
                if (diff_added is not None or diff_removed is not None)
                else None
            ),
            "skills": [s["skill_name"] for s in skills],
            "skillsDetail": skills,
        })

    return result
