from pathlib import Path
import sqlite3
import os

# Default database path (can be overridden in tests)
DEFAULT_DB = Path(os.getenv("APP_DB_PATH", "local_storage.db"))

def connect(db_path: str | Path | None = None) -> sqlite3.Connection:
    """Open a SQLite connection that respects APP_DB_PATH during tests."""
    target = str(db_path) if db_path is not None else os.getenv("APP_DB_PATH", "local_storage.db")

    # Create directory if needed
    if target != ":memory:":
        Path(target).parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(target)
    conn.execute("PRAGMA foreign_keys=ON;")
    if target != ":memory:":
        conn.execute("PRAGMA journal_mode=WAL;")  # skip WAL for in-memory DBs
    conn.execute("PRAGMA synchronous=NORMAL;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """
    Create initial schema: includes consent_log and users table for week-1.
    """
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            display_name TEXT,
            email TEXT
        );

        CREATE TABLE IF NOT EXISTS consent_log (
            consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL DEFAULT 1,
            status     TEXT NOT NULL CHECK (status IN ('accepted','rejected')),
            timestamp  TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_consent_user_time
            ON consent_log(user_id, timestamp);

        -- ADD OTHER TABLES HERE (future milestones)
        """
    )

    # Ensure one default user entry
    cur = conn.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        conn.execute("INSERT INTO users(display_name) VALUES (?)", ("local-user",))
    conn.commit()
