from pathlib import Path
import sqlite3
import os
from typing import Optional, Tuple, Dict
from datetime import datetime

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
    """Create all tables and indexes if they don't exist."""
    cur = conn.cursor()

    # --- USERS TABLE ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
        username  TEXT,
        email     TEXT
    );
    """)

    # Unique index so usernames cannot duplicate (case-insensitive)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_nocase
        ON users(LOWER(username));
    """)

    # --- CONSENT LOG TABLE ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS consent_log (
        consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id    INTEGER NOT NULL DEFAULT 1,
        status     TEXT NOT NULL CHECK (status IN ('accepted','rejected')),
        timestamp  TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Index for quick "latest consent per user" lookup
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_consent_user_time
        ON consent_log(user_id, timestamp);
    """)

    # --- EXTERNAL CONSENT TABLE ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS external_consent (
        consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        status TEXT NOT NULL CHECK(status IN ('accepted','rejected')),
        timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );
    """)

    # Mirror index for fast "latest external consent per user"
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_external_user_time
        ON external_consent(user_id, timestamp);
    """)

    # Add a view for latest user consents
    cur.execute("""
    CREATE VIEW IF NOT EXISTS latest_user_consents AS
    SELECT 
        u.user_id,
        u.username,
        (
            SELECT c.status
            FROM consent_log c
            WHERE c.user_id = u.user_id
            ORDER BY c.timestamp DESC
            LIMIT 1
        ) AS latest_consent,
        (
            SELECT e.status
            FROM external_consent e
            WHERE e.user_id = u.user_id
            ORDER BY e.timestamp DESC
            LIMIT 1
        ) AS latest_external_consent
    FROM users u
    ORDER BY u.user_id;
    """)

    # --- FILES TABLE ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS files (
        file_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL,
        file_name   TEXT NOT NULL,
        file_path   TEXT,
        extension   TEXT,
        file_type   TEXT,
        size_bytes  INTEGER,
        created     TEXT,
        modified    TEXT,
        project_name TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    # Index for faster file lookups (requires user id and file name)
    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_files_user 
        ON files(user_id, file_name)
    """)

    # --- PROJECT CLASSIFICATIONS TABLE ---
    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_classifications (
        classification_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id           INTEGER NOT NULL,
        zip_path          TEXT NOT NULL,
        zip_name          TEXT NOT NULL,
        project_name      TEXT NOT NULL,
        classification    TEXT NOT NULL CHECK (classification IN ('individual','collaborative')),
        project_type      TEXT CHECK (project_type IN ('code', 'text')),
        recorded_at       TEXT NOT NULL,
        UNIQUE(user_id, zip_name, project_name),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_project_classifications_lookup
        ON project_classifications(user_id, zip_name);
    """)

    conn.commit()

# ----------------------------------------------------------

def _normalize_username(u: str) -> str:
    """Clean username for consistent lookup."""
    return u.strip()

def get_user_by_username(conn: sqlite3.Connection, username: str) -> Optional[Tuple[int, str, Optional[str]]]:
    """Case-insensitive lookup."""
    norm = _normalize_username(username)
    row = conn.execute(
        "SELECT user_id, username, email FROM users WHERE LOWER(username)=LOWER(?)",
        (norm,),
    ).fetchone()
    return row if row else None

def get_or_create_user(conn: sqlite3.Connection, username: str, email: Optional[str] = None) -> int:
    """Return existing user_id or create new user."""
    existing = get_user_by_username(conn, username)
    if existing:
        return existing[0]
    cur = conn.execute(
        "INSERT INTO users (username, email) VALUES (?, ?)",
        (username.strip(), email),
    )
    conn.commit()
    return cur.lastrowid

def get_latest_consent(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    """Return most recent consent status for a user."""
    row = conn.execute(
        "SELECT status FROM consent_log WHERE user_id=? ORDER BY timestamp DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return row[0] if row else None

def get_latest_external_consent(conn: sqlite3.Connection, user_id: int) -> Optional[str]:
    """Return most recent external consent status for a user."""
    row = conn.execute(
        "SELECT status FROM external_consent WHERE user_id=? ORDER BY timestamp DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    return row[0] if row else None

def store_parsed_files(conn: sqlite3.Connection, files_info: list[dict], user_id: int) -> None:
    # Insert parsed metadata into the 'files' table
    # Each file is linked to the user

    if not files_info:
        return # nothing to insert
    
    cur = conn.cursor()
    for f in files_info:
        cur.execute("""
            INSERT INTO files (
                user_id, file_name, file_path, extension, file_type, size_bytes, created, modified, project_name
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            f.get("file_name"),
            f.get("file_path"),
            f.get("extension"),
            f.get("file_type"),
            f.get("size_bytes"),
            f.get("created"),
            f.get("modified"),
            f.get("project_name"),
        ))
    
    conn.commit()


def record_project_classification(
    conn: sqlite3.Connection,
    user_id: int,
    zip_path: str,
    zip_name: str,
    project_name: str,
    classification: str,
    when: datetime | None = None
) -> None:
    """Persist a single project classification selection."""
    if classification not in {"individual", "collaborative"}:
        raise ValueError("classification must be 'individual' or 'collaborative'")

    timestamp = (when or datetime.now()).isoformat()
    conn.execute(
        """
        INSERT INTO project_classifications (
            user_id, zip_path, zip_name, project_name, classification, recorded_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, zip_name, project_name) DO UPDATE SET
            classification=excluded.classification,
            recorded_at=excluded.recorded_at
        """,
        (user_id, zip_path, zip_name, project_name, classification, timestamp),
    )
    conn.commit()


def record_project_classifications(
    conn: sqlite3.Connection,
    user_id: int,
    zip_path: str,
    zip_name: str,
    assignments: Dict[str, str],
    when: datetime | None = None,
) -> None:
    """Bulk helper that stores classifications for multiple project names."""
    for project_name, classification in assignments.items():
        record_project_classification(
            conn,
            user_id,
            zip_path,
            zip_name,
            project_name,
            classification,
            when=when,
        )


def get_project_classifications(
    conn: sqlite3.Connection,
    user_id: int,
    zip_name: str,
) -> dict[str, str]:
    """Fetch saved classifications for a given user + uploaded ZIP."""
    rows = conn.execute(
        """
        SELECT project_name, classification
        FROM project_classifications
        WHERE user_id=? AND zip_name=?
        """,
        (user_id, zip_name),
    ).fetchall()
    return {project_name: classification for project_name, classification in rows}
    
