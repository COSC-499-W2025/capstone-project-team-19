-- src/db/schema/tables.sql

-- Defines all database tables, indexes, and views used across the system.
-- Loaded automatically by db/connection.py during initialization.


-- USERS & CONSENT TABLES

CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT,
    email     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_nocase
    ON users(LOWER(username));

CREATE TABLE IF NOT EXISTS consent_log (
    consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL DEFAULT 1,
    status     TEXT NOT NULL CHECK (status IN ('accepted','rejected')),
    timestamp  TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_consent_user_time
    ON consent_log(user_id, timestamp);

CREATE TABLE IF NOT EXISTS external_consent (
    consent_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL CHECK(status IN ('accepted','rejected')),
    timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE INDEX IF NOT EXISTS idx_external_user_time
    ON external_consent(user_id, timestamp);

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


-- FILES & PROJECT CLASSIFICATIONS

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

CREATE INDEX IF NOT EXISTS idx_files_user 
    ON files(user_id, file_name);

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

CREATE INDEX IF NOT EXISTS idx_project_classifications_lookup
    ON project_classifications(user_id, zip_name);

CREATE TABLE IF NOT EXISTS config_files (
    config_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    project_name  TEXT,
    file_name     TEXT NOT NULL,
    file_path     TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);


-- TEXT ANALYSIS (LLM + NON-LLM)

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

-- CODE METRICS TABLE

CREATE TABLE IF NOT EXISTS non_llm_code_individual(
    metrics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    classification_id INTEGER NOT NULL,
    total_files INTEGER,
    total_lines INTEGER,
    total_code_lines INTEGER,
    total_comments INTEGER,
    comment_ratio REAL,
    total_functions INTEGER,
    avg_complexity REAL,
    avg_maintainability REAL,
    functions_needing_refactor INTEGER,
    high_complexity_files INTEGER,
    low_maintainability_files INTEGER,
    radon_details_json TEXT,
    lizard_details_json TEXT,
    generated_at TEXT DEFAULT(datetime('now')),
    UNIQUE(metrics_id),
    FOREIGN KEY (classification_id) REFERENCES project_classifications(classification_id) ON DELETE CASCADE

);


-- TEXT CONTRIBUTION TABLES

CREATE TABLE IF NOT EXISTS text_contribution_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    drive_file_id TEXT NOT NULL,
    revision_id TEXT NOT NULL,
    words_added INTEGER NOT NULL DEFAULT 0,
    revision_text TEXT,  -- optional, only exists for Google Doc, NULL otherwise
    revision_timestamp TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS text_contribution_summary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    drive_file_id TEXT NOT NULL,
    user_revision_count INTEGER NOT NULL DEFAULT 0,
    total_word_count INTEGER NOT NULL DEFAULT 0,
    total_revision_count INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(user_id, project_name, drive_file_id)
);


-- INTEGRATIONS (TOKENS, GITHUB, DRIVE)

CREATE TABLE IF NOT EXISTS user_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, provider)
);

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

CREATE TABLE IF NOT EXISTS github_repo_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,

    total_commits INTEGER,
    commit_days INTEGER,
    first_commit_date TEXT,
    last_commit_date TEXT,

    issues_opened INTEGER,
    issues_closed INTEGER,

    prs_opened INTEGER,
    prs_merged INTEGER,

    total_additions INTEGER,
    total_deletions INTEGER,
    contribution_percent REAL,

    team_total_commits INTEGER,
    team_total_additions INTEGER,
    team_total_deletions INTEGER,

    last_synced TEXT DEFAULT (datetime('now')),

    UNIQUE (user_id, project_name, repo_owner, repo_name)
);

-- PROJECT SUMMARIES

CREATE TABLE IF NOT EXISTS project_summaries (
    project_summary_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    project_name        TEXT NOT NULL,
    project_type        TEXT,
    project_mode        TEXT,
    summary_json        TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, project_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    skill_name TEXT NOT NULL,
    level TEXT NOT NULL,
    score REAL NOT NULL,
    evidence_json TEXT,
    UNIQUE(user_id, project_name, skill_name),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

-- USER FILE CONTRIBUTIONS (for collaborative projects)
-- Tracks which files each user worked on, used to filter skill detection

CREATE TABLE IF NOT EXISTS user_code_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    file_path TEXT NOT NULL,
    lines_changed INTEGER DEFAULT 0,  -- additions + deletions
    commits_count INTEGER DEFAULT 0,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, project_name, file_path),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS github_collaboration_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    UNIQUE (user_id, project_name, repo_owner, repo_name)
);

CREATE TABLE IF NOT EXISTS github_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    issue_title TEXT,
    issue_body TEXT,
    labels_json TEXT,
    created_at TEXT,
    closed_at TEXT,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_issues_lookup
    ON github_issues(user_id, project_name, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_issue_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    issue_number INTEGER NOT NULL,
    comment_body TEXT,
    created_at TEXT,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_issue_comments_lookup
    ON github_issue_comments(user_id, project_name, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_pull_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER,
    pr_title TEXT,
    pr_body TEXT,
    labels_json TEXT,
    created_at TEXT,
    merged_at TEXT,
    state TEXT,
    merged INTEGER DEFAULT 0,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_prs_lookup
    ON github_pull_requests(user_id, project_name, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_commit_timestamps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    commit_timestamp TEXT NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_commit_timestamps_lookup
    ON github_commit_timestamps(user_id, project_name, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_pr_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    review_json TEXT NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_pr_reviews_lookup
    ON github_pr_reviews(user_id, project_name, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_pr_review_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_name TEXT NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    comment_json TEXT NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_pr_review_comments_lookup
    ON github_pr_review_comments(user_id, project_name, repo_owner, repo_name);


-- TEXT ACTIVITY TYPE CONTRIBUTION DATA

CREATE TABLE IF NOT EXISTS text_activity_contribution (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    classification_id INTEGER UNIQUE NOT NULL,
    start_date TEXT,
    end_date TEXT,
    duration_days INTEGER,
    total_files INTEGER,
    classified_files INTEGER,
    activity_classification_json TEXT,  
    timeline_json TEXT,               
    activity_counts_json TEXT,     
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (classification_id) REFERENCES project_classifications(classification_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_text_activity_contribution_lookup
    ON text_activity_contribution(classification_id);
-- Code activity metrics (per user, project, scope, and source)
CREATE TABLE IF NOT EXISTS code_activity_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,     -- who + which project
    project_name TEXT    NOT NULL,
    scope        TEXT    NOT NULL,  -- 'individual' or 'collaborative'
    source       TEXT    NOT NULL,  -- where this metric comes from: 'files', 'prs', or 'combined'
    activity_type TEXT   NOT NULL,  -- 'feature_coding', 'refactoring', 'debugging', 'testing', 'documentation'
    event_count  INTEGER NOT NULL,
    total_events INTEGER NOT NULL,
    percent      REAL    NOT NULL,  -- 0–100
    recorded_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);
