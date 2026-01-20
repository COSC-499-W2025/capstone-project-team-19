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
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    conn.execute("PRAGMA foreign_keys=ON;")
    if target != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Create all tables and indexes if they don't exist."""
    schema_path = Path(__file__).parent / "schema" / "tables.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    conn.executescript(schema_sql)
    conn.commit()
    print(f"Initialized database schema from {schema_path}")
