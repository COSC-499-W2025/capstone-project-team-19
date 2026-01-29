from __future__ import annotations

from sqlite3 import Connection
from typing import Any, Dict, List, Optional

from src.db import (
    set_project_rank,
    clear_project_rank,
    clear_all_rankings,
    bulk_set_rankings,
    get_project_summary_by_id
)
from src.insights.rank_projects.rank_project_importance import collect_project_ranking_rows


def get_project_ranking(conn: Connection, user_id: int) -> List[Dict[str, Any]]:
    """
    Returns sorted ranking rows (including score + manual rank).
    """
    return collect_project_ranking_rows(conn, user_id, respect_manual_ranking=True)


def replace_project_ranking(conn: Connection, user_id: int, project_ids: List[int]) -> None:
    """
    Replace the ENTIRE manual ranking order for this user.

    Behavior:
    - Clears all existing manual ranks
    - Sets manual_rank = 1..N according to the provided project_ids order
    """
    if len(project_ids) != len(set(project_ids)):
        raise ValueError("Duplicate project IDs are not allowed")

    # Validate all ids exist + belong to user, and map to names
    names: List[str] = []
    for pid in project_ids:
        row = get_project_summary_by_id(conn, user_id, pid)
        if not row:
            raise KeyError(f"Project not found: {pid}")
        names.append(row["project_name"])

    clear_all_rankings(conn, user_id)
    rankings = [(name, rank) for rank, name in enumerate(names, start=1)]
    bulk_set_rankings(conn, user_id, rankings)


def set_project_manual_rank(conn: Connection, user_id: int, project_id: int, rank: Optional[int]) -> None:
    """
    Patch one project's manual rank. If rank is None, clears manual ranking for that project.
    """
    row = get_project_summary_by_id(conn, user_id, project_id)
    if not row:
        raise KeyError(f"Project not found: {project_id}")
    project_name = row["project_name"]

    if rank is None:
        clear_project_rank(conn, user_id, project_name)
        return

    set_project_rank(conn, user_id, project_name, rank)


def reset_project_ranking(conn: Connection, user_id: int) -> None:
    """
    Clears all manual ranking for the user (reverts to pure auto ranking).
    """
    clear_all_rankings(conn, user_id)

