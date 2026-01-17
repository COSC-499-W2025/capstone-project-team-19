"""
src/db/resumes.py

Helpers for storing and retrieving frozen resume snapshots.
"""
from __future__ import annotations

import sqlite3
from typing import Dict, List, Any, Optional

from src.db.code_activity import get_code_activity_percents, get_normalized_code_metrics
from src.db import get_classification_id
from src.db.text_activity import get_text_activity_contribution

def insert_resume_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    name: str,
    resume_json: str,
    rendered_text: Optional[str] = None,
) -> int:
    """
    Insert a new resume snapshot. Returns the inserted row id.
    """
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO resume_snapshots (user_id, name, resume_json, rendered_text)
        VALUES (?, ?, ?, ?)
        """,
        (user_id, name, resume_json, rendered_text),
    )
    conn.commit()
    return cur.lastrowid


def list_resumes(conn: sqlite3.Connection, user_id: int) -> List[Dict[str, Any]]:
    """
    List stored resume snapshots for a user, newest first.
    """
    rows = conn.execute(
        """
        SELECT id, name, created_at
        FROM resume_snapshots
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user_id,),
    ).fetchall()
    return [{"id": r[0], "name": r[1], "created_at": r[2]} for r in rows]


def get_resume_snapshot(conn: sqlite3.Connection, user_id: int, resume_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a specific resume snapshot by id for a user.
    """
    row = conn.execute(
        """
        SELECT id, name, resume_json, rendered_text, created_at
        FROM resume_snapshots
        WHERE user_id = ? AND id = ?
        """,
        (user_id, resume_id),
    ).fetchone()

    if not row:
        return None

    return {
        "id": row[0],
        "name": row[1],
        "resume_json": row[2],
        "rendered_text": row[3],
        "created_at": row[4],
    }

def update_resume_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    resume_id: int,
    resume_json: str,
    rendered_text: Optional[str] = None,
) -> None:
    """
    Update an existing resume snapshot's JSON + rendered text.
    """
    conn.execute(
        """
        UPDATE resume_snapshots
        SET resume_json = ?, rendered_text = ?
        WHERE user_id = ? AND id = ?
        """,
        (resume_json, rendered_text, user_id, resume_id),
    )
    conn.commit()


def delete_resume_snapshot(
    conn: sqlite3.Connection,
    user_id: int,
    resume_id: int,
) -> None:
    """
    Permanently delete a resume snapshot for a user.
    """
    conn.execute(
        """
        DELETE FROM resume_snapshots
        WHERE user_id = ? AND id = ?
        """,
        (user_id, resume_id),
    )
    conn.commit()

def build_contribution_bullets(
    conn: sqlite3.Connection,
    user_id: int,
    project: Dict[str, Any],
) -> List[str]:
    """
    Return the same style of 'Contributed ...' bullets that the app prints,
    but as a structured list stored in resume_json.
    """
    ptype = project.get("project_type")
    project_name = project.get("project_name") or ""
    if not project_name:
        return []

    if ptype == "code":
        is_collab = bool(project.get("project_mode") == "collaborative")
        metrics = get_normalized_code_metrics(conn, user_id, project_name, is_collab)
        activities = get_code_activity_percents(conn, user_id, project_name, source="combined")
        if not metrics:
            return ["(no metrics found in code_collaborative_metrics / git_individual_metrics)"]

        total_commits = int(metrics["total_commits"])
        your_commits = int(metrics["your_commits"])
        loc_added = int(metrics["loc_added"])
        loc_deleted = int(metrics["loc_deleted"])
        loc_net = int(metrics["loc_net"])

        share = (your_commits / total_commits * 100.0) if total_commits > 0 else 0.0

        activity_label = {
            "feature_coding": "feature implementation",
            "refactoring": "refactoring",
            "debugging": "debugging",
            "testing": "testing",
            "documentation": "documentation",
        }
        top_acts = [
            (k, v) for k, v in sorted(activities.items(), key=lambda kv: kv[1], reverse=True)
            if float(v or 0.0) > 0.0
        ][:3]
        workflows = ", ".join(activity_label.get(k, k.replace("_", " ")) for k, _ in top_acts) if top_acts else "core development"

        bullets: List[str] = []
        if is_collab:
            bullets.append(
                f"Contributed {share:.1f}% of total repository commits ({your_commits} commits) across {workflows} workflows."
            )
        else:
            bullets.append(
                f"Delivered {your_commits} commits across {workflows} workflows in an individual codebase."
            )

        bullets.append(
            f"Delivered a net code contribution of {loc_net:+d} lines, adding {loc_added} and deleting {loc_deleted}, "
            f"demonstrating an emphasis on maintainability and code quality."
        )

        feat = float(activities.get("feature_coding") or 0.0)
        refac = float(activities.get("refactoring") or 0.0)
        debug = float(activities.get("debugging") or 0.0)
        test = float(activities.get("testing") or 0.0)
        doc = float(activities.get("documentation") or 0.0)

        if feat > 0.0:
            bullets.append(f"Focused {feat:.1f}% of development effort on feature implementation, translating requirements into production-ready code.")
        if refac > 0.0:
            bullets.append(f"Allocated {refac:.1f}% of contributions to refactoring, improving readability, modularity, and long-term maintainability.")
        if debug > 0.0:
            bullets.append(f"Dedicated {debug:.1f}% of activity to debugging, identifying root causes and resolving runtime and logic issues.")
        if (test + doc) > 0.0:
            bullets.append(f"Contributed to testing and documentation ({(test + doc):.1f}% combined), supporting code reliability and team onboarding.")

        return bullets

    if ptype == "text":
        # Use snapshot-provided classification_id if present; otherwise resolve it.
        classification_id = project.get("classification_id")
        if not classification_id:
            classification_id = get_classification_id(conn, user_id, project_name)

        bullets: List[str] = []
        pct = project.get("contribution_percent")
        if isinstance(pct, (int, float)):
            bullets.append(f"Contributed to {pct:.1f}% of the project deliverables.")

        row = get_text_activity_contribution(conn, classification_id) if classification_id else None
        if not row:
            if not bullets:
                bullets.append("(no activity breakdown found in text_activity_contribution)")
            return bullets

        summary = row.get("summary", {}) or {}
        counts = (summary.get("activity_counts", {}) or {})
        duration_days = (row.get("timestamp_analysis", {}) or {}).get("duration_days")

        if isinstance(duration_days, int) and duration_days > 0:
            bullets.append(f"Worked across a {duration_days}-day timeline.")

        total_events = sum(int(v or 0) for v in counts.values())
        if total_events > 0:
            ranked = sorted(counts.items(), key=lambda kv: int(kv[1] or 0), reverse=True)
            top = [(k, int(v or 0)) for k, v in ranked if int(v or 0) > 0][:3]
            if len(top) >= 2:
                (a1, c1), (a2, c2) = top[0], top[1]
                p1 = c1 / total_events * 100.0
                p2 = c2 / total_events * 100.0
                if len(top) >= 3:
                    a3, c3 = top[2]
                    p3 = c3 / total_events * 100.0
                    bullets.append(
                        f"Balanced {str(a1).lower()} ({p1:.1f}%) with {str(a2).lower()} ({p2:.1f}%), and {str(a3).lower()} ({p3:.1f}%), "
                        f"supporting both content development and iterative improvement."
                    )
                else:
                    bullets.append(
                        f"Balanced {str(a1).lower()} ({p1:.1f}%) with {str(a2).lower()} ({p2:.1f}%), supporting both content development and iterative improvement."
                    )

            for stage in ("Revision", "Final"):
                if int(counts.get(stage, 0) or 0) > 0:
                    bullets.append(f"Contributed to {stage.lower()}-stage work, strengthening clarity, structure, and polish.")
                    break

        if not bullets:
            bullets.append("(no activity breakdown found in text_activity_contribution)")
        return bullets

    return []