import json
from sqlite3 import Connection
from typing import Any, Dict, List, Optional

from src.insights.rank_projects.rank_project_importance import collect_project_ranking_rows
from src.services.project_dates_service import compute_project_dates
from src.services.resumes_service import get_resume_by_id


# ---------------------------------------------------------------------------
# Portfolio-level settings
# ---------------------------------------------------------------------------

def get_portfolio_settings(conn: Connection, user_id: int) -> Dict[str, Any]:
    row = conn.execute(
        "SELECT portfolio_public, active_resume_id FROM portfolio_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    if row is None:
        return {"portfolio_public": False, "active_resume_id": None}
    return {
        "portfolio_public": bool(row["portfolio_public"]),
        "active_resume_id": row["active_resume_id"],
    }


def is_portfolio_public(conn: Connection, user_id: int) -> bool:
    row = conn.execute(
        "SELECT portfolio_public FROM portfolio_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    return bool(row["portfolio_public"]) if row else False


def upsert_portfolio_settings(
    conn: Connection,
    user_id: int,
    portfolio_public: Optional[bool] = None,
    active_resume_id: Optional[int] = None,
    clear_active_resume: bool = False,
) -> Dict[str, Any]:
    existing = conn.execute(
        "SELECT portfolio_public, active_resume_id FROM portfolio_settings WHERE user_id = ?",
        (user_id,),
    ).fetchone()

    current_public = bool(existing["portfolio_public"]) if existing else False
    current_resume_id = existing["active_resume_id"] if existing else None

    new_public = portfolio_public if portfolio_public is not None else current_public
    if clear_active_resume:
        new_resume_id = None
    elif active_resume_id is not None:
        new_resume_id = active_resume_id
    else:
        new_resume_id = current_resume_id

    conn.execute(
        """
        INSERT INTO portfolio_settings (user_id, portfolio_public, active_resume_id, updated_at)
        VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(user_id) DO UPDATE SET
            portfolio_public = excluded.portfolio_public,
            active_resume_id = excluded.active_resume_id,
            updated_at = excluded.updated_at
        """,
        (user_id, int(new_public), new_resume_id),
    )
    conn.commit()
    return {"portfolio_public": new_public, "active_resume_id": new_resume_id}


# ---------------------------------------------------------------------------
# Per-project visibility
# ---------------------------------------------------------------------------

def set_project_visibility(
    conn: Connection, user_id: int, project_summary_id: int, is_public: bool
) -> bool:
    cur = conn.execute(
        """
        UPDATE project_summaries
        SET is_public = ?
        WHERE user_id = ? AND project_summary_id = ?
        """,
        (int(is_public), user_id, project_summary_id),
    )
    conn.commit()
    return cur.rowcount > 0


# ---------------------------------------------------------------------------
# Public read methods
# ---------------------------------------------------------------------------

def get_public_projects(conn: Connection, user_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            ps.project_summary_id,
            p.display_name AS project_name,
            ps.project_type,
            ps.project_mode,
            ps.created_at
        FROM project_summaries ps
        JOIN projects p ON p.project_key = ps.project_key
        WHERE ps.user_id = ? AND ps.is_public = 1
        ORDER BY ps.created_at DESC, p.display_name ASC
        """,
        (user_id,),
    ).fetchall()
    return [dict(row) for row in rows]


def get_public_project_detail(
    conn: Connection, user_id: int, project_summary_id: int
) -> Optional[Dict[str, Any]]:
    row = conn.execute(
        """
        SELECT
            ps.project_summary_id,
            p.display_name AS project_name,
            ps.project_type,
            ps.project_mode,
            ps.summary_json,
            ps.created_at,
            ps.manual_start_date,
            ps.manual_end_date
        FROM project_summaries ps
        JOIN projects p ON p.project_key = ps.project_key
        WHERE ps.user_id = ? AND ps.project_summary_id = ? AND ps.is_public = 1
        """,
        (user_id, project_summary_id),
    ).fetchone()

    if not row:
        return None

    try:
        summary_dict = json.loads(row["summary_json"])
    except (json.JSONDecodeError, TypeError):
        summary_dict = {}

    manual_overrides = summary_dict.get("manual_overrides") or {}
    contributions = summary_dict.get("contributions") or {}
    dates = compute_project_dates(
        conn=conn,
        user_id=user_id,
        project_summary_id=row["project_summary_id"],
        project_name=row["project_name"],
        project_type=row["project_type"],
        project_mode=row["project_mode"],
    )

    return {
        "project_summary_id": row["project_summary_id"],
        "project_name": row["project_name"],
        "project_type": row["project_type"],
        "project_mode": row["project_mode"],
        "created_at": row["created_at"],
        "start_date": dates.start_date,
        "end_date": dates.end_date,
        "summary_text": manual_overrides.get("summary_text") or summary_dict.get("summary_text"),
        "contribution_summary": contributions.get("manual_contribution_summary"),
        "languages": summary_dict.get("languages", []),
        "frameworks": summary_dict.get("frameworks", []),
        "skills": summary_dict.get("skills", []),
    }


def get_public_ranking(conn: Connection, user_id: int) -> List[Dict[str, Any]]:
    public_ids = {
        row[0]
        for row in conn.execute(
            "SELECT project_summary_id FROM project_summaries WHERE user_id = ? AND is_public = 1",
            (user_id,),
        ).fetchall()
    }

    all_rows = collect_project_ranking_rows(conn, user_id, respect_manual_ranking=True)
    public_rows = [r for r in all_rows if r["project_summary_id"] in public_ids]

    return [
        {
            "rank": i + 1,
            "project_summary_id": r["project_summary_id"],
            "project_name": r["project_name"],
        }
        for i, r in enumerate(public_rows)
    ]


def get_public_resume_by_id(
    conn: Connection, user_id: int, resume_id: int
) -> Optional[Dict[str, Any]]:
    resume = get_resume_by_id(conn, user_id, resume_id)
    if not resume:
        return None

    public_projects = [
        {
            "project_name": p.get("project_name"),
            "project_type": p.get("project_type"),
            "project_mode": p.get("project_mode"),
            "languages": p.get("languages", []),
            "frameworks": p.get("frameworks", []),
            "summary_text": p.get("summary_text"),
            "skills": p.get("skills", []),
            "key_role": p.get("key_role"),
            "contribution_bullets": p.get("contribution_bullets", []),
            "start_date": p.get("start_date"),
            "end_date": p.get("end_date"),
        }
        for p in resume.get("projects", [])
    ]

    return {
        "id": resume["id"],
        "name": resume["name"],
        "created_at": resume.get("created_at"),
        "projects": public_projects,
        "aggregated_skills": resume.get("aggregated_skills", {}),
        "rendered_text": resume.get("rendered_text"),
    }


def get_public_skills(conn: Connection, user_id: int) -> List[Dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT
            ps.skill_name,
            ps.level,
            p.display_name AS project_name
        FROM project_skills ps
        JOIN project_summaries psum
            ON ps.user_id = psum.user_id AND ps.project_key = psum.project_key
        JOIN projects p
            ON ps.project_key = p.project_key
        WHERE ps.user_id = ? AND psum.is_public = 1 AND ps.score > 0
        ORDER BY ps.score DESC
        """,
        (user_id,),
    ).fetchall()
    return [{"skill_name": row[0], "level": row[1], "project_name": row[2]} for row in rows]
