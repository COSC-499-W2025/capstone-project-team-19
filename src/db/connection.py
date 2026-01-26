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


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes if they don't exist."""
    schema_path = Path(__file__).parent / "schema" / "tables.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)

    # Version-scoping for project versions/deduplication flows
    _ensure_column(conn, "files", "version_key", "INTEGER")

    # Indexes that reference migrated columns should be created after migrations.
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_files_user_project_version ON files(user_id, project_name, version_key)"
    )

    conn.commit()
    print(f"Initialized database schema from {schema_path}")
