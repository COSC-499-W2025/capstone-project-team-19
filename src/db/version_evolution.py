"""
src/db/version_evolution.py

Per-version evolution data for project evolution showcase.
Feeds: GET /projects/{id}/evolution, future skills timeline, heatmap.
"""

import json
import sqlite3
from typing import Any, Dict, List, Optional

from .projects import get_project_key


def insert_version_summary(
    conn: sqlite3.Connection,
    version_key: int,
    summary_text: Optional[str] = None,
    activity_date: Optional[str] = None,
    lines_added: Optional[int] = None,
    lines_deleted: Optional[int] = None,
    total_words: Optional[int] = None,
    languages: Optional[List[str]] = None,
    frameworks: Optional[List[str]] = None,
    avg_complexity: Optional[float] = None,
    total_files: Optional[int] = None,
) -> None:
    """Snapshot version-level summary, diff stats, and enriched metrics."""
    conn.execute(
        """
        INSERT OR REPLACE INTO version_summaries
            (version_key, summary_text, activity_date,
             lines_added, lines_deleted, total_words,
             languages_json, frameworks_json, avg_complexity, total_files)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            version_key,
            summary_text or None,
            activity_date,
            lines_added,
            lines_deleted,
            total_words,
            json.dumps(languages) if languages else None,
            json.dumps(frameworks) if frameworks else None,
            avg_complexity,
            total_files,
        ),
    )
    conn.commit()


def insert_version_skills_from_project(conn: sqlite3.Connection, user_id: int, project_name: str, version_key: int) -> None:
    """Copy current project_skills into version_skills for this version."""
    project_key = get_project_key(conn, user_id, project_name)
    if project_key is None:
        return
    rows = conn.execute(
        """
        SELECT skill_name, level, score
        FROM project_skills
        WHERE user_id = ? AND project_key = ? AND score > 0
        """,
        (user_id, int(project_key)),
    ).fetchall()
    if not rows:
        return
    conn.executemany(
        """
        INSERT OR REPLACE INTO version_skills (version_key, skill_name, level, score)
        VALUES (?, ?, ?, ?)
        """,
        [(version_key, r[0], r[1], r[2]) for r in rows],
    )
    conn.commit()


def get_version_summary(conn: sqlite3.Connection, version_key: int) -> Optional[Dict[str, Any]]:
    """Get version_summaries row for a version."""
    row = conn.execute(
        """
        SELECT summary_text, activity_date, lines_added, lines_deleted,
               total_words, created_at, languages_json, frameworks_json,
               avg_complexity, total_files
        FROM version_summaries WHERE version_key = ?
        """,
        (version_key,),
    ).fetchone()
    if not row:
        return None
    return {
        "summary_text": row[0],
        "activity_date": row[1],
        "lines_added": row[2],
        "lines_deleted": row[3],
        "total_words": row[4],
        "created_at": row[5],
        "languages": json.loads(row[6]) if row[6] else [],
        "frameworks": json.loads(row[7]) if row[7] else [],
        "avg_complexity": row[8],
        "total_files": row[9],
    }


def get_version_skills(conn: sqlite3.Connection, version_key: int) -> List[Dict[str, Any]]:
    """Get skills for a version."""
    rows = conn.execute(
        """
        SELECT skill_name, level, score
        FROM version_skills
        WHERE version_key = ?
        ORDER BY score DESC
        """,
        (version_key,),
    ).fetchall()
    return [{"skill_name": r[0], "level": r[1], "score": r[2]} for r in rows]


def get_version_keys_ordered_for_project(conn: sqlite3.Connection, project_key: int) -> List[tuple[int, str]]:
    """
    Return (version_key, created_at) for all versions of a project, oldest first.
    """
    rows = conn.execute(
        """
        SELECT version_key, created_at
        FROM project_versions
        WHERE project_key = ?
        ORDER BY version_key ASC
        """,
        (project_key,),
    ).fetchall()
    return [(int(r[0]), r[1] or "") for r in rows]


# Cross-version comparison helpers (computed from existing tables)

def get_version_files_count(conn: sqlite3.Connection, version_key: int) -> Optional[int]:
    """Return the number of files for a version, or None if no row."""
    row = conn.execute(
        "SELECT COUNT(*) FROM version_files WHERE version_key = ?",
        (version_key,),
    ).fetchone()
    return int(row[0]) if row else None


def get_file_diff_between_versions(conn: sqlite3.Connection, prev_version_key: int, curr_version_key: int) -> Dict[str, Any]:
    """Compare version_files rows to find added/modified/removed files."""
    prev_rows = conn.execute(
        "SELECT relpath, file_hash FROM version_files WHERE version_key = ?",
        (prev_version_key,),
    ).fetchall()

    curr_rows = conn.execute(
        "SELECT relpath, file_hash FROM version_files WHERE version_key = ?",
        (curr_version_key,),
    ).fetchall()

    prev_map = {r[0]: r[1] for r in prev_rows}
    curr_map = {r[0]: r[1] for r in curr_rows}

    added = sorted(p for p in curr_map if p not in prev_map)
    removed = sorted(p for p in prev_map if p not in curr_map)
    modified = sorted(
        p for p in curr_map
        if p in prev_map and curr_map[p] != prev_map[p]
    )
    unchanged_count = sum(
        1 for p in curr_map
        if p in prev_map and curr_map[p] == prev_map[p]
    )

    return {
        "added": added,
        "modified": modified,
        "removed": removed,
        "unchanged_count": unchanged_count,
    }


def get_skill_diff_between_versions(conn: sqlite3.Connection, prev_version_key: int, curr_version_key: int) -> Dict[str, Any]:
    """Compare version_skills rows to find new/improved/declined/removed skills."""
    prev_skills = {
        r[0]: {"level": r[1], "score": r[2]}
        for r in conn.execute(
            "SELECT skill_name, level, score FROM version_skills WHERE version_key = ?",
            (prev_version_key,),
        ).fetchall()
    }
    curr_skills = {
        r[0]: {"level": r[1], "score": r[2]}
        for r in conn.execute(
            "SELECT skill_name, level, score FROM version_skills WHERE version_key = ?",
            (curr_version_key,),
        ).fetchall()
    }

    new_skills = [
        {"skill_name": s, "prev_score": None, "score": curr_skills[s]["score"], "level": curr_skills[s]["level"]}
        for s in sorted(curr_skills.keys() - prev_skills.keys())
    ]
    removed_skills = [
        {"skill_name": s, "prev_score": prev_skills[s]["score"], "score": prev_skills[s]["score"], "level": prev_skills[s]["level"]}
        for s in sorted(prev_skills.keys() - curr_skills.keys())
    ]
    improved = []
    declined = []
    for s in sorted(curr_skills.keys() & prev_skills.keys()):
        skill_difference = curr_skills[s]["score"] - prev_skills[s]["score"]
        if skill_difference > 0:
            improved.append({
                "skill_name": s,
                "prev_score": prev_skills[s]["score"],
                "score": curr_skills[s]["score"],
                "level": curr_skills[s]["level"],
            })
        elif skill_difference < 0:
            declined.append({
                "skill_name": s,
                "prev_score": prev_skills[s]["score"],
                "score": curr_skills[s]["score"],
                "level": curr_skills[s]["level"],
            })

    return {
        "new": new_skills,
        "removed": removed_skills,
        "improved": improved,
        "declined": declined,
    }
