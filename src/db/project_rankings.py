import sqlite3
from typing import Optional, List, Tuple


def set_project_rank(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    manual_rank: Optional[int]
) -> None:
    if manual_rank is None:
        # If setting to NULL (auto-ranking), just clear the rank
        clear_project_rank(conn, user_id, project_name)
        return
    # Get current rank of this project (if any)
    current_rank = get_project_rank(conn, user_id, project_name)
    if current_rank == manual_rank:
        # No change needed
        return
    # Shift all projects at the target rank (and above) down by 1
    # Exclude the current project to avoid self-shifting
    conn.execute("""
        UPDATE project_rankings
        SET manual_rank = manual_rank + 1,
            updated_at = datetime('now')
        WHERE user_id = ?
          AND manual_rank >= ?
          AND project_name != ?
    """, (user_id, manual_rank, project_name))

    # Now set the new rank for this project
    conn.execute("""
        INSERT INTO project_rankings (user_id, project_name, manual_rank)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, project_name) DO UPDATE SET
            manual_rank = excluded.manual_rank,
            updated_at = datetime('now')
    """, (user_id, project_name, manual_rank))

    conn.commit()


def get_project_rank(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str
) -> Optional[int]:
    row = conn.execute("""
        SELECT manual_rank
        FROM project_rankings
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name)).fetchone()

    return row[0] if row else None


def get_all_project_ranks(
    conn: sqlite3.Connection,
    user_id: int
) -> List[Tuple[str, Optional[int]]]:
    rows = conn.execute("""
        SELECT project_name, manual_rank
        FROM project_rankings
        WHERE user_id = ?
        ORDER BY manual_rank ASC NULLS LAST
    """, (user_id,)).fetchall()

    return rows


def clear_project_rank(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str
) -> None:
    conn.execute("""
        DELETE FROM project_rankings
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name))
    conn.commit()


def clear_all_rankings(
    conn: sqlite3.Connection,
    user_id: int
) -> None:
    conn.execute("""
        DELETE FROM project_rankings
        WHERE user_id = ?
    """, (user_id,))
    conn.commit()


def bulk_set_rankings(
    conn: sqlite3.Connection,
    user_id: int,
    rankings: List[Tuple[str, int]]
) -> None:
    for project_name, rank in rankings:
        # Use direct SQL to bypass the shifting logic in set_project_rank
        conn.execute("""
            INSERT INTO project_rankings (user_id, project_name, manual_rank)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id, project_name) DO UPDATE SET
                manual_rank = excluded.manual_rank,
                updated_at = datetime('now')
        """, (user_id, project_name, rank))
    conn.commit()
