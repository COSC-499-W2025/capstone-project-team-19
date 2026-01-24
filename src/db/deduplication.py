import sqlite3

def find_existing_version_by_strict_fp(conn, user_id: int, fp_strict: str):
    row = conn.execute(
        """
        SELECT pv.project_key, pv.version_key
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = ? AND pv.fingerprint_strict = ?
        LIMIT 1
        """,
        (user_id, fp_strict),
    ).fetchone()
    return (row[0], row[1]) if row else None

def find_existing_version_by_loose_fp(conn, user_id: int, fp_loose: str):
    """Find exact duplicate based on content-only fingerprint (ignores file paths).
    
    This detects when the exact same files are uploaded with different filenames/paths.
    """
    row = conn.execute(
        """
        SELECT pv.project_key, pv.version_key
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = ? AND pv.fingerprint_loose = ?
        LIMIT 1
        """,
        (user_id, fp_loose),
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

def get_relpath_set_for_version(conn, version_key: int) -> set[str]:
    rows = conn.execute(
        "SELECT relpath FROM version_files WHERE version_key = ?",
        (version_key,),
    ).fetchall()
    return {r[0] for r in rows}


# writing to db for duplication checks

#Create a new logical project. Returns project_key.
def insert_project(conn, user_id: int, display_name: str) -> int:
    cur = conn.execute(
        "INSERT INTO projects(user_id, display_name) VALUES(?, ?)",
        (user_id, display_name),
    )
    return int(cur.lastrowid)

# Create a new version under an existing project. Returns version_key.
def insert_project_version(
    conn,
    project_key: int,
    upload_id,
    fingerprint_strict: str,
    fingerprint_loose: str,
) -> int:
    cur = conn.execute(
        """
        INSERT INTO project_versions(
            project_key,
            upload_id,
            fingerprint_strict,
            fingerprint_loose
        )
        VALUES (?, ?, ?, ?)
        """,
        (project_key, upload_id, fingerprint_strict, fingerprint_loose),
    )
    return int(cur.lastrowid)

# Insert all (relpath, file_hash) pairs for a version.
def insert_version_files(
    conn,
    version_key: int,
    entries: list[tuple[str, str]],
) -> None:
    conn.executemany(
        """
        INSERT INTO version_files(version_key, relpath, file_hash)
        VALUES (?, ?, ?)
        """,
        [(version_key, rel, h) for (rel, h) in entries],
    )