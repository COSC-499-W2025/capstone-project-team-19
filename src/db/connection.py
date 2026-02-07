"""
src/db/connection.py

Handles database connection setup and schema initialization.
Responsible for:
 - Creating SQLite connections
 - Loading and executing schema definitions from tables.sql
"""

import sqlite3
from pathlib import Path
import os


DEFAULT_DB = Path(os.getenv("APP_DB_PATH", "local_storage.db"))

def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    target = str(db_path) if db_path is not None else os.getenv("APP_DB_PATH", "local_storage.db")
    if target != ":memory:":
        Path(target).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target)
    conn.execute("PRAGMA foreign_keys=ON;")
    if target != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def _column_names(conn: sqlite3.Connection, table: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    # PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
    return {r[1] for r in rows} if rows else set()


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, ddl: str) -> None:
    """
    Add a column to an existing table if it's missing.
    `ddl` should be the column definition part, e.g. "INTEGER" or "TEXT DEFAULT ''".
    """
    cols = _column_names(conn, table)
    if column in cols:
        return
    conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}")


def _backfill_extraction_root(conn: sqlite3.Connection) -> None:
    """
    Best-effort migration:
    - Ensures `project_versions.extraction_root` exists
    - Backfills it from `files.file_path` for each version_key

    Rationale:
    Legacy/CLI flows can create `project_versions` without `upload_id`, so we cannot
    always locate extracted files via `uploads.zip_path`. Storing `extraction_root`
    lets downstream analysis locate `src/analysis/zip_data/<extraction_root>/...`.
    """
    _ensure_column(conn, "project_versions", "extraction_root", "TEXT")

    missing = conn.execute(
        """
        SELECT version_key
        FROM project_versions
        WHERE extraction_root IS NULL OR extraction_root = ''
        """
    ).fetchall()

    for (version_key,) in missing:
        sample = conn.execute(
            """
            SELECT file_path
            FROM files
            WHERE version_key = ? AND file_path IS NOT NULL AND file_path != ''
            ORDER BY file_id DESC
            LIMIT 1
            """,
            (int(version_key),),
        ).fetchone()

        if not sample or not sample[0]:
            continue

        raw = str(sample[0]).replace("\\", "/")
        root = raw.split("/", 1)[0].strip()
        if not root:
            continue

        conn.execute(
            "UPDATE project_versions SET extraction_root = ? WHERE version_key = ?",
            (root, int(version_key)),
        )


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes if they don't exist."""
    schema_path = Path(__file__).parent / "schema" / "tables.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)

    # Legacy migration: ensure version_key exists on files (schema now has version_key, no project_name)
    _ensure_column(conn, "files", "version_key", "INTEGER")

    # Store extraction folder name for legacy versions (no upload_id linkage)
    _backfill_extraction_root(conn)

    conn.commit()
    print(f"Initialized database schema from {schema_path}")
