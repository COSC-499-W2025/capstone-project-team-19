import sqlite3
from typing import List, Dict, Any, Optional, Literal


def get_user_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    # First try exact context match
    if context_id is not None:
        cursor = conn.execute(
            """
            SELECT skill_name, is_highlighted, display_order
            FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id = ?
            ORDER BY display_order ASC NULLS LAST, skill_name ASC
            """,
            (user_id, context, context_id)
        )
    else:
        cursor = conn.execute(
            """
            SELECT skill_name, is_highlighted, display_order
            FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id IS NULL
            ORDER BY display_order ASC NULLS LAST, skill_name ASC
            """,
            (user_id, context)
        )

    rows = cursor.fetchall()

    if not rows and context != "global":
        cursor = conn.execute(
            """
            SELECT skill_name, is_highlighted, display_order
            FROM user_skill_preferences
            WHERE user_id = ? AND context = 'global' AND context_id IS NULL
            ORDER BY display_order ASC NULLS LAST, skill_name ASC
            """,
            (user_id,)
        )
        rows = cursor.fetchall()

    return [
        {
            "skill_name": row[0],
            "is_highlighted": bool(row[1]),
            "display_order": row[2],
        }
        for row in rows
    ]


def get_highlighted_skill_names(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> List[str]:
    prefs = get_user_skill_preferences(conn, user_id, context, context_id)
    return [
        p["skill_name"]
        for p in prefs
        if p["is_highlighted"]
    ]


def upsert_skill_preference(
    conn: sqlite3.Connection,
    user_id: int,
    skill_name: str,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
    is_highlighted: bool = True,
    display_order: Optional[int] = None,
) -> None:
    if context_id is not None:
        conn.execute(
            """
            INSERT INTO user_skill_preferences
                (user_id, context, context_id, skill_name, is_highlighted, display_order, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, context, context_id, skill_name)
            DO UPDATE SET
                is_highlighted = excluded.is_highlighted,
                display_order = excluded.display_order,
                updated_at = datetime('now')
            """,
            (user_id, context, context_id, skill_name, int(is_highlighted), display_order)
        )
    else:
        conn.execute(
            """
            INSERT INTO user_skill_preferences
                (user_id, context, context_id, skill_name, is_highlighted, display_order, updated_at)
            VALUES (?, ?, NULL, ?, ?, ?, datetime('now'))
            ON CONFLICT(user_id, context, context_id, skill_name)
            DO UPDATE SET
                is_highlighted = excluded.is_highlighted,
                display_order = excluded.display_order,
                updated_at = datetime('now')
            """,
            (user_id, context, skill_name, int(is_highlighted), display_order)
        )
    conn.commit()


def bulk_upsert_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    preferences: List[Dict[str, Any]],
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> None:
    for pref in preferences:
        upsert_skill_preference(
            conn=conn,
            user_id=user_id,
            skill_name=pref["skill_name"],
            context=context,
            context_id=context_id,
            is_highlighted=pref.get("is_highlighted", True),
            display_order=pref.get("display_order"),
        )


def delete_skill_preference(
    conn: sqlite3.Connection,
    user_id: int,
    skill_name: str,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> bool:
    if context_id is not None:
        cursor = conn.execute(
            """
            DELETE FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id = ? AND skill_name = ?
            """,
            (user_id, context, context_id, skill_name)
        )
    else:
        cursor = conn.execute(
            """
            DELETE FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id IS NULL AND skill_name = ?
            """,
            (user_id, context, skill_name)
        )
    conn.commit()
    return cursor.rowcount > 0


def clear_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> int:
    if context_id is not None:
        cursor = conn.execute(
            """
            DELETE FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id = ?
            """,
            (user_id, context, context_id)
        )
    else:
        cursor = conn.execute(
            """
            DELETE FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id IS NULL
            """,
            (user_id, context)
        )
    conn.commit()
    return cursor.rowcount


def get_all_user_skills(
    conn: sqlite3.Connection,
    user_id: int,
) -> List[str]:
    cursor = conn.execute(
        """
        SELECT DISTINCT skill_name
        FROM project_skills
        WHERE user_id = ? AND score > 0
        ORDER BY skill_name ASC
        """,
        (user_id,)
    )
    return [row[0] for row in cursor.fetchall()]


def has_skill_preferences(
    conn: sqlite3.Connection,
    user_id: int,
    context: Literal["global", "portfolio", "resume"] = "global",
    context_id: Optional[int] = None,
) -> bool:
    if context_id is not None:
        cursor = conn.execute(
            """
            SELECT 1 FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id = ?
            LIMIT 1
            """,
            (user_id, context, context_id)
        )
    else:
        cursor = conn.execute(
            """
            SELECT 1 FROM user_skill_preferences
            WHERE user_id = ? AND context = ? AND context_id IS NULL
            LIMIT 1
            """,
            (user_id, context)
        )
    return cursor.fetchone() is not None
