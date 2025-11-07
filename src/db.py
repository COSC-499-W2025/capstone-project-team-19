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
    CREATE TABLE IF NOT EXISTS config_files (
        config_id     INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id       INTEGER NOT NULL,
        project_name  TEXT,
        file_name     TEXT NOT NULL,
        file_path     TEXT,
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE INDEX IF NOT EXISTS idx_project_classifications_lookup
        ON project_classifications(user_id, zip_name);
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_tokens(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        provider TEXT NOT NULL,
        access_token TEXT,
        refresh_token TEXT,
        expires_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, provider)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_repos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_name TEXT NOT NULL,
        provider TEXT NOT NULL,
        repo_url TEXT NOT NULL,
        linked_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, project_name, provider),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS project_drive_files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_name TEXT NOT NULL,
        local_file_name TEXT NOT NULL,
        drive_file_id TEXT NOT NULL,
        drive_file_name TEXT,
        mime_type TEXT,
        status TEXT NOT NULL CHECK (status IN ('auto_matched', 'manual_selected', 'not_found')),
        linked_at TEXT DEFAULT (datetime('now')),
        UNIQUE(user_id, project_name, local_file_name),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS github_accounts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        github_username TEXT NOT NULL,
        github_id INTEGER NOT NULL,
        github_name TEXT NOT NULL,
        github_email TEXT,
        github_profile_url TEXT,
        UNIQUE (user_id, github_username),
        FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
    );
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
    """
    Insert parsed metadata into the 'files' table.
    Config files are inserted into 'config_files' instead.
    Each file is linked to the user.
    """

    if not files_info:
        return # nothing to insert
    
    cur = conn.cursor()
    for f in files_info:
        # Store config files in config_files table
        if f.get("file_type") == "config":
            cur.execute("""
                INSERT INTO config_files (
                    user_id, project_name, file_name, file_path
                ) VALUES (?, ?, ?, ?)
            """, (
                user_id,
                f.get("project_name"),
                f.get("file_name"),
                f.get("file_path"),
            ))
        else:
            #Store regular files in files table
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
    
def save_token_placeholder(conn: sqlite3.Connection, user_id: int):
    conn.execute("""
        INSERT OR IGNORE INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', 'PENDING_OAUTH')
    """, (user_id,))

    conn.commit()

def save_project_repo(conn: sqlite3.Connection, user_id: int, project_name: str, repo_url: str, provider="github"):
    # Store which GitHub repository corresponds to a given collaborative project
    
    conn.execute("""
        INSERT OR REPLACE INTO project_repos (user_id, project_name, provider, repo_url)
        VALUES (?, ?, ?, ?)
    """, (user_id, project_name, provider, repo_url))

    conn.commit()


def get_project_repo(conn: sqlite3.Connection, user_id: int, project_name: str, provider="github") -> Optional[str]:
    # Fetch mapped GitHub repo URL for this project, if exists
    
    row = conn.execute("""
        SELECT repo_url FROM project_repos
        WHERE user_id=? AND project_name=? AND provider=?
        LIMIT 1
    """, (user_id, project_name, provider)).fetchone()

    return row[0] if row else None


def store_file_link(conn: sqlite3.Connection,user_id: int,project_name: str,local_file_name: str,drive_file_id: str,drive_file_name: Optional[str] = None,mime_type: Optional[str] = None,status: str = 'auto_matched') -> None:
    """
    Store a link between a local ZIP file and a Google Drive file.
    Status must be one of: 'auto_matched', 'manual_selected', 'not_found'
    
    Uses UNIQUE constraint to prevent duplicates: (user_id, project_name, local_file_name)
    """
    if status not in {'auto_matched', 'manual_selected', 'not_found'}:
        raise ValueError("status must be 'auto_matched', 'manual_selected', or 'not_found'")
    
    # Delete any existing entry for this file first (to ensure clean state)
    conn.execute("""
        DELETE FROM project_drive_files
        WHERE user_id=? AND project_name=? AND local_file_name=?
    """, (user_id, project_name, local_file_name))
    
    # Insert new entry
    conn.execute("""
        INSERT INTO project_drive_files (
            user_id, project_name, local_file_name, drive_file_id,
            drive_file_name, mime_type, status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, project_name, local_file_name, drive_file_id, drive_file_name, mime_type, status))
    conn.commit()


def get_project_drive_files(conn: sqlite3.Connection, user_id: int, project_name: str) -> list[dict]:
    """
    Get all linked Drive files for a project.
    Returns list of dicts with keys: local_file_name, drive_file_id, drive_file_name, mime_type, status
    """
    rows = conn.execute("""
        SELECT local_file_name, drive_file_id, drive_file_name, mime_type, status
        FROM project_drive_files
        WHERE user_id=? AND project_name=?
        ORDER BY linked_at
    """, (user_id, project_name)).fetchall()
    
    return [
        {
            'local_file_name': row[0],
            'drive_file_id': row[1],
            'drive_file_name': row[2],
            'mime_type': row[3],
            'status': row[4]
        }
        for row in rows
    ]


def get_unlinked_project_files(conn: sqlite3.Connection, user_id: int, project_name: str) -> list[str]:
    """
    Get list of local file names that have status 'not_found' (couldn't be linked).
    """
    rows = conn.execute("""
        SELECT local_file_name
        FROM project_drive_files
        WHERE user_id=? AND project_name=? AND status='not_found'
        ORDER BY linked_at
    """, (user_id, project_name)).fetchall()
    
    return [row[0] for row in rows]

def store_github_account(conn, user_id, github_user):
    conn.execute("""
        INSERT OR REPLACE INTO github_accounts
        (user_id, github_username, github_id, github_name, github_email, github_profile_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, github_user["login"], github_user["id"], github_user["name"], github_user["email"], github_user["profile_url"]
    ))
    conn.commit()