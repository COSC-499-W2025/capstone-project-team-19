"""
Database operations for tracking user file contributions in collaborative projects.
"""

import sqlite3
from typing import List, Dict


def store_file_contributions(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    file_contributions: Dict[str, Dict[str, int]]
) -> None:
    """
    Store which files a user worked on in a collaborative project.

    Args:
        conn: Database connection
        user_id: User ID
        project_name: Project name
        file_contributions: Dict mapping file_path -> {"lines_changed": int, "commits_count": int}

    Example:
        file_contributions = {
            "src/main.py": {"lines_changed": 150, "commits_count": 5},
            "src/utils.py": {"lines_changed": 80, "commits_count": 2},
        }
    """
    cursor = conn.cursor()

    for file_path, stats in file_contributions.items():
        lines_changed = stats.get("lines_changed", 0)
        commits_count = stats.get("commits_count", 0)

        cursor.execute("""
            INSERT OR REPLACE INTO user_file_contributions (
                user_id,
                project_name,
                file_path,
                lines_changed,
                commits_count,
                recorded_at
            ) VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """, (user_id, project_name, file_path, lines_changed, commits_count))

    conn.commit()
    print(f"[DB] Stored contributions for {len(file_contributions)} files in '{project_name}'")


def get_user_contributed_files(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str,
    min_lines: int = 0
) -> List[str]:
    """
    Get list of file paths the user contributed to in a collaborative project.

    Args:
        conn: Database connection
        user_id: User ID
        project_name: Project name
        min_lines: Minimum lines changed to consider (default 0 = all files)

    Returns:
        List of file paths (e.g., ["src/main.py", "src/utils.py"])
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT file_path
        FROM user_file_contributions
        WHERE user_id = ? AND project_name = ? AND lines_changed >= ?
        ORDER BY lines_changed DESC
    """, (user_id, project_name, min_lines))

    return [row[0] for row in cursor.fetchall()]


def get_file_contribution_stats(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str
) -> Dict[str, Dict[str, int]]:
    """
    Get detailed contribution stats for all files in a project.

    Returns:
        Dict mapping file_path -> {"lines_changed": int, "commits_count": int}
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT file_path, lines_changed, commits_count
        FROM user_file_contributions
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name))

    stats = {}
    for file_path, lines_changed, commits_count in cursor.fetchall():
        stats[file_path] = {
            "lines_changed": lines_changed,
            "commits_count": commits_count
        }

    return stats


def has_contribution_data(
    conn: sqlite3.Connection,
    user_id: int,
    project_name: str
) -> bool:
    """
    Check if we have contribution data for this project.

    Returns:
        True if contribution data exists, False otherwise
    """
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*) FROM user_file_contributions
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name))

    count = cursor.fetchone()[0]
    return count > 0
