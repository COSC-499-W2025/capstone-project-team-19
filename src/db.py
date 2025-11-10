from pathlib import Path
import sqlite3
import os
from typing import Optional, Tuple, Dict, Any
import json
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
    CREATE TABLE IF NOT EXISTS non_llm_text (
        metrics_id        INTEGER PRIMARY KEY AUTOINCREMENT,
        classification_id INTEGER UNIQUE NOT NULL,
        doc_count         INTEGER,
        total_words       INTEGER,
        reading_level_avg REAL,
        reading_level_label TEXT,
        keywords_json     TEXT,
        summary_json      TEXT,
        generated_at      TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (classification_id) REFERENCES project_classifications(classification_id) ON DELETE CASCADE
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
        repo_full_name TEXT,
        repo_owner TEXT,
        repo_name TEXT,
        repo_id INTEGER,
        default_branch TEXT,
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

    cur.execute("""CREATE TABLE IF NOT EXISTS text_contribution_revisions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        drive_file_id TEXT NOT NULL,
        revision_id TEXT NOT NULL,
        words_added INTEGER NOT NULL DEFAULT 0,
        revision_text TEXT,  -- optional, only exists for Google Doc, NULL otherwise
        revision_timestamp TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    );""")

    cur.execute("""CREATE TABLE IF NOT EXISTS text_contribution_summary (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_name TEXT NOT NULL,
        drive_file_id TEXT NOT NULL,
        user_revision_count INTEGER NOT NULL DEFAULT 0,
        total_word_count INTEGER NOT NULL DEFAULT 0,   -- total words user added
        total_revision_count INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        UNIQUE(user_id, project_name, drive_file_id)
    );""")

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

    #TODO: normalize the github metrics into reltional tables, instead of one big JSON text dump
    cur.execute("""
    CREATE TABLE IF NOT EXISTS github_repo_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,

        user_id INTEGER NOT NULL,
        project_name TEXT NOT NULL,
        repo_owner TEXT NOT NULL,
        repo_name TEXT NOT NULL,
        metrics_json TEXT NOT NULL,
        UNIQUE (user_id, project_name, repo_owner, repo_name)
    );
    """)
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS llm_text (
        text_metric_id INTEGER PRIMARY KEY AUTOINCREMENT,
        classification_id INTEGER NOT NULL,
        file_path TEXT,
        file_name TEXT,
        project_name TEXT,
        word_count INTEGER,
        sentence_count INTEGER,
        flesch_kincaid_grade REAL,
        lexical_diversity REAL,
        summary TEXT NOT NULL,
        skills_json JSON,
        strength_json JSON,
        weaknesses_json JSON,
        overall_score TEXT,
        processed_at TEXT DEFAULT (datetime('now')),
        UNIQUE(text_metric_id),
        FOREIGN KEY (classification_id) REFERENCES project_classifications(classification_id) ON DELETE CASCADE
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


def get_classification_id(conn: sqlite3.Connection, user_id: int, project_name: str) -> Optional[int]:
    row = conn.execute(
        """
        SELECT classification_id
        FROM project_classifications
        WHERE user_id = ? AND project_name = ?
        ORDER BY recorded_at DESC
        LIMIT 1
        """,
        (user_id, project_name),
    ).fetchone()
    return row[0] if row else None


def store_text_offline_metrics(
    conn: sqlite3.Connection,
    classification_id: int,
    project_metrics: dict | None,
) -> None:
    if not classification_id or not project_metrics:
        return

    summary_block = project_metrics.get("summary") or {}
    keywords = project_metrics.get("keywords")

    doc_count = summary_block.get("total_documents")
    total_words = summary_block.get("total_words")
    reading_level_avg = summary_block.get("reading_level_average")
    reading_level_label = summary_block.get("reading_level_label")

    summary_json = json.dumps(project_metrics, ensure_ascii=False)
    keywords_json = json.dumps(keywords, ensure_ascii=False) if keywords is not None else None

    existing = conn.execute(
        """
        SELECT doc_count,
               total_words,
               reading_level_avg,
               reading_level_label,
               keywords_json,
               summary_json
        FROM non_llm_text
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    if existing:
        doc_count = doc_count if doc_count is not None else existing[0]
        total_words = total_words if total_words is not None else existing[1]
        reading_level_avg = reading_level_avg if reading_level_avg is not None else existing[2]
        reading_level_label = reading_level_label if reading_level_label is not None else existing[3]
        keywords_json = keywords_json if keywords_json is not None else existing[4]
        summary_json = summary_json if summary_json is not None else existing[5]

        conn.execute(
            """
            UPDATE non_llm_text
            SET doc_count = ?,
                total_words = ?,
                reading_level_avg = ?,
                reading_level_label = ?,
                keywords_json = ?,
                summary_json = ?,
                generated_at = datetime('now')
            WHERE classification_id = ?
            """,
            (
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
                classification_id,
            ),
        )
    else:
        if keywords_json is None:
            keywords_json = json.dumps([], ensure_ascii=False)
        if summary_json is None:
            summary_json = json.dumps({}, ensure_ascii=False)

        conn.execute(
            """
            INSERT INTO non_llm_text (
                classification_id,
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
                generated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                classification_id,
                doc_count,
                total_words,
                reading_level_avg,
                reading_level_label,
                keywords_json,
                summary_json,
            ),
        )
    conn.commit()
    
def store_text_llm_metrics(conn: sqlite3.Connection, classification_id: int, project_name: str, file_name:str, file_path:str, linguistic:dict, summary: str, skills: list, success: dict )-> None:
    skills_json=json.dumps(skills)
    strength_json=json.dumps(success.get("strengths", []))
    weaknesses_json=json.dumps(success.get("weaknesses", []))
    conn.execute(
        """
        INSERT INTO llm_text(
        classification_id, file_path, file_name, project_name, word_count, sentence_count, flesch_kincaid_grade, lexical_diversity, summary, skills_json, strength_json, weaknesses_json, overall_score)
        VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (classification_id, file_path, file_name, project_name, linguistic.get("word_count"), linguistic.get("sentence_count"), linguistic.get("flesch_kincaid_grade"), linguistic.get("lexical_diversity"), summary, skills_json, strength_json, weaknesses_json, success.get("score"))
        )
    conn.commit()

def get_text_llm_metrics(conn: sqlite3.Connection, classification_id: int) -> Optional[dict]:
    row = conn.execute("""
        SELECT text_metric_id, classification_id, project_name, file_name, file_path, word_count, sentence_count, flesch_kincaid_grade, lexical_diversity,
        summary, skills_json, strength_json, weaknesses_json, overall_score, processed_at
        FROM llm_text
        WHERE classification_id = ?
    """, (classification_id,)).fetchone()

    if not row:
        return None

    return {
        "text_metric_id": row[0],
        "classification_id": row[1],
        "project_name": row[2],
        "file_name": row[3],
        "file_path": row[4],
        "word_count": row[5],
        "sentence_count": row[6],
        "flesch_kincaid_grade": row[7],
        "lexical_diversity": row[8],
        "summary": row[9],
        "skills_json": row[10],
        "strength_json": row[11],
        "weaknesses_json": row[12],
        "overall_score": row[13],
        "processed_at": row[14]
    }

def get_classification_id(conn: sqlite3.Connection, user_id: int, project_name: str)->Optional[int]:
    row=conn.execute("""
    SELECT classification_id FROM project_classifications
    WHERE user_id=? AND project_name=?
    ORDER BY recorded_at DESC
    LIMIT 1
""", (user_id,project_name)).fetchone()
    
    return row[0] if row else None

def save_token_placeholder(conn: sqlite3.Connection, user_id: int):
    conn.execute("""
        INSERT OR IGNORE INTO user_tokens (user_id, provider, access_token)
        VALUES (?, 'github', 'PENDING_OAUTH')
    """, (user_id,))

    conn.commit()

def save_project_repo(conn: sqlite3.Connection, user_id: int, project_name: str, repo_url: str, repo_full_name: str, repo_owner: str, repo_name: str, repo_id: int, default_branch: str, provider="github"):
    # Store which GitHub repository corresponds to a given collaborative project
    
    conn.execute("""
        INSERT OR REPLACE INTO project_repos (
            user_id, 
            project_name, 
            provider, 
            repo_url,
            repo_full_name,
            repo_owner,
            repo_name,
            repo_id,
            default_branch
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (user_id, project_name, provider, repo_url, repo_full_name, repo_owner, repo_name, repo_id, default_branch))

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

def store_text_contribution_revision(conn: sqlite3.Connection, revision: Dict[str, Any]) -> None:
    """
    Store a text contribution revision record.
    """
    timestamp = revision.get("revision_timestamp")
    if hasattr(timestamp, "isoformat"):
        timestamp = timestamp.isoformat()
    conn.execute("""
        INSERT INTO text_contribution_revisions (
            user_id, drive_file_id, revision_id, words_added, revision_text, revision_timestamp
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        revision["user_id"],
        revision["drive_file_id"],
        revision["revision_id"],
        revision.get("words_added", 0),
        revision.get("revision_text"),
        timestamp,
    ))
    conn.commit()

def store_text_contribution_summary(conn: sqlite3.Connection, summary: Dict[str, Any]) -> None:
    """
    Store or update a text contribution summary record.
    """
    conn.execute("""
        INSERT INTO text_contribution_summary (
            user_id, project_name, drive_file_id, user_revision_count, total_word_count, total_revision_count
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, drive_file_id) DO UPDATE SET
            user_revision_count=excluded.user_revision_count,
            total_word_count=excluded.total_word_count,
            total_revision_count=excluded.total_revision_count
    """, (
        summary["user_id"],
        summary["project_name"],
        summary["drive_file_id"],
        summary.get("user_revision_count", 0),
        summary.get("total_word_count", 0),
        summary.get("total_revision_count", 0),
    ))
    conn.commit()

def store_github_account(conn, user_id, github_user):
    conn.execute("""
        INSERT OR REPLACE INTO github_accounts
        (user_id, github_username, github_id, github_name, github_email, github_profile_url)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        user_id, github_user["login"], github_user["id"], github_user["name"], github_user["email"], github_user["profile_url"]
    ))
    conn.commit()
