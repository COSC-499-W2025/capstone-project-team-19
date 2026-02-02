import sqlite3
from typing import Optional, List, Tuple


def shift_project_ranks_for_insert(conn: sqlite3.Connection, user_id: int, manual_rank: int) -> None:
    """
    Shift everything at/after the target rank down (increase by 1).
    """
    conn.execute(
        """
        UPDATE project_rankings
        SET manual_rank = manual_rank + 1,
            updated_at = datetime('now')
        WHERE user_id = ?
          AND manual_rank >= ?
        """,
        (user_id, manual_rank),
    )

def shift_project_ranks_for_move_up(
    conn: sqlite3.Connection,
    user_id: int,
    new_rank: int,
    current_rank: int,
    project_name: str,
) -> None:
    """
    Move up: shift ranks [new_rank, current_rank-1] down (increase by 1).
    """
    conn.execute(
        """
        UPDATE project_rankings
        SET manual_rank = manual_rank + 1,
            updated_at = datetime('now')
        WHERE user_id = ?
          AND manual_rank >= ?
          AND manual_rank < ?
          AND project_name != ?
        """,
        (user_id, new_rank, current_rank, project_name),
    )

def shift_project_ranks_for_move_down(
    conn: sqlite3.Connection,
    user_id: int,
    current_rank: int,
    new_rank: int,
    project_name: str,
) -> None:
    """
    Move down: shift ranks [current_rank+1, new_rank] up (decrease by 1).
    """
    conn.execute(
        """
        UPDATE project_rankings
        SET manual_rank = manual_rank - 1,
            updated_at = datetime('now')
        WHERE user_id = ?
          AND manual_rank > ?
          AND manual_rank <= ?
          AND project_name != ?
        """,
        (user_id, current_rank, new_rank, project_name),
    )


def upsert_project_rank(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    manual_rank: int,
) -> None:
    conn.execute(
        """
        INSERT INTO project_rankings (user_id, project_name, manual_rank)
        VALUES (?, ?, ?)
        ON CONFLICT(user_id, project_name) DO UPDATE SET
            manual_rank = excluded.manual_rank,
            updated_at = datetime('now')
        """,
        (user_id, project_name, manual_rank),
    )


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


def clear_all_rankings(
    conn: sqlite3.Connection,
    user_id: int
) -> None:
    conn.execute("""
        DELETE FROM project_rankings
        WHERE user_id = ?
    """, (user_id,))


def bulk_set_rankings(
    conn: sqlite3.Connection,
    user_id: int,
    rankings: List[Tuple[str, int]]
) -> None:
    for project_name, rank in rankings:
        # Direct SQL (no shifting logic here by design)
        upsert_project_rank(conn, user_id, project_name, rank)
