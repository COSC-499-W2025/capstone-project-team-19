import sqlite3

def find_existing_version_by_strict_fp(conn, user_id: int, fp_strict: str):
    row = conn.execute(
        """
        SELECT pv.project_key, pv.version_key
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p-user_id = ? AND pv.fingerprint_strict = ?
        LIMIT 1
        """,
        (user_id, fp_strict),
    ).fetchone()
    return (row[0], row[1]) if row else None

def get_latest_versions(conn, user_id: int):
    rows = conn.execute(
        """
        SELECT p.project_key, MAX(pv.version_key) AS latest_version_key
        FROM projects p
        JOIN project_versions pv ON pv.project_key = p.project_key
        WHERE p.user_id = ?
        GROUP BY p.project_key
        """,
        (user_id,),
    ).fetchall()
    return {project_key: latest_vk for project_key, latest_vk in rows}

def get_hash_set_for_version(conn, version_key: int) -> set[str]:
    rows = conn.execute(
        "SELECT file_hash FROM version_files WHERE version_key = ?",
        (version_key,),
    ).fetchall()
    return {r[0] for r in rows}