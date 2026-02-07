-- src/db/schema/tables.sql

-- Defines all database tables, indexes, and views used across the system.
-- Loaded automatically by db/connection.py during initialization.


-- USERS & CONSENT TABLES

CREATE TABLE IF NOT EXISTS users (
    user_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    username  TEXT UNIQUE,
    email     TEXT,
    hashed_password TEXT
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
-- Files are versioned only: each row belongs to one project_version (no project_name).

CREATE TABLE IF NOT EXISTS files (
    file_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id     INTEGER NOT NULL,
    version_key INTEGER NOT NULL,
    file_name   TEXT NOT NULL,
    file_path   TEXT,
    extension   TEXT,
    file_type   TEXT,
    size_bytes  INTEGER,
    created     TEXT,
    modified    TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (version_key) REFERENCES project_versions(version_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_files_user
    ON files(user_id, file_name);

CREATE INDEX IF NOT EXISTS idx_files_user_version
    ON files(user_id, version_key);

CREATE TABLE IF NOT EXISTS projects (
    project_key INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    display_name TEXT NOT NULL,
    classification TEXT CHECK (classification IN ('individual','collaborative')),
    project_type TEXT CHECK (project_type IN ('code', 'text')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_user_display_name
ON projects(user_id, display_name);

CREATE TABLE IF NOT EXISTS project_versions (
    version_key INTEGER PRIMARY KEY AUTOINCREMENT,
    project_key INTEGER NOT NULL,
    upload_id INTEGER,
    extraction_root TEXT,
    fingerprint_strict TEXT NOT NULL,
    fingerprint_loose TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_key) REFERENCES projects(project_key)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_versions_unique_strict 
    ON project_versions(project_key, fingerprint_strict);

CREATE TABLE IF NOT EXISTS version_files (
    version_key INTEGER NOT NULL,
    relpath TEXT NOT NULL,
    file_hash TEXT NOT NULL,
    PRIMARY KEY (version_key, relpath),
    FOREIGN KEY (version_key) REFERENCES project_versions(version_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_version_files_hash 
    ON version_files(file_hash);

CREATE INDEX IF NOT EXISTS idx_version_files_version 
    ON version_files(version_key);


CREATE TABLE IF NOT EXISTS config_files (
    config_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    project_key   INTEGER NOT NULL,
    file_name     TEXT NOT NULL,
    file_path     TEXT,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);


-- TEXT ANALYSIS (LLM + NON-LLM)

CREATE TABLE IF NOT EXISTS non_llm_text (
    metrics_id        INTEGER PRIMARY KEY AUTOINCREMENT,
    version_key       INTEGER UNIQUE NOT NULL,
    doc_count         INTEGER, -- always 1 (main file)
    total_words       INTEGER, -- of main file
    reading_level_avg REAL, -- of main file
    reading_level_label TEXT, -- of main file
    keywords_json     TEXT, -- currently empty in case we want to bring back TF IDF to determine user's "topics of interest"
    summary_json      TEXT,
    csv_metadata TEXT,
    generated_at      TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (version_key) REFERENCES project_versions(version_key) ON DELETE CASCADE
);

-- CODE METRICS TABLE

CREATE TABLE IF NOT EXISTS non_llm_code_individual(
    metrics_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_key INTEGER NOT NULL,
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
    FOREIGN KEY (version_key) REFERENCES project_versions(version_key) ON DELETE CASCADE

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
    project_key INTEGER NOT NULL,
    drive_file_id TEXT NOT NULL,
    user_revision_count INTEGER NOT NULL DEFAULT 0,
    total_word_count INTEGER NOT NULL DEFAULT 0,
    total_revision_count INTEGER NOT NULL DEFAULT 0,
    UNIQUE(user_id, project_key, drive_file_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
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
    project_key INTEGER NOT NULL,
    provider TEXT NOT NULL,
    repo_url TEXT NOT NULL,
    repo_full_name TEXT,
    repo_owner TEXT,
    repo_name TEXT,
    repo_id INTEGER,
    default_branch TEXT,
    linked_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, project_key, provider),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_drive_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    local_file_name TEXT NOT NULL,
    drive_file_id TEXT NOT NULL,
    drive_file_name TEXT,
    mime_type TEXT,
    status TEXT NOT NULL CHECK (status IN ('auto_matched', 'manual_selected', 'not_found')),
    linked_at TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, project_key, local_file_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
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
    project_key INTEGER NOT NULL,
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

    UNIQUE (user_id, project_key, repo_owner, repo_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_repo_metrics_lookup
    ON github_repo_metrics (user_id, project_key, repo_owner, repo_name);

-- GIT INDIVIDUAL METRICS (for local git repository analysis)
CREATE TABLE IF NOT EXISTS git_individual_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,

    -- Commit statistics
    total_commits INTEGER,
    first_commit_date TEXT,
    last_commit_date TEXT,
    time_span_days INTEGER,
    average_commits_per_week REAL,
    average_commits_per_month REAL,
    unique_authors INTEGER,

    -- Code change summary
    total_lines_added INTEGER,
    total_lines_deleted INTEGER,
    net_lines_changed INTEGER,
    total_weeks_active INTEGER,

    -- Activity patterns
    total_active_days INTEGER,
    total_active_months INTEGER,
    average_commits_per_active_day REAL,
    busiest_day TEXT,
    busiest_day_commits INTEGER,
    busiest_month TEXT,
    busiest_month_commits INTEGER,

    last_analyzed TEXT DEFAULT (datetime('now')),

    UNIQUE (user_id, project_key),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_git_individual_metrics_user_project
    ON git_individual_metrics (user_id, project_key);

-- PROJECT SUMMARIES

CREATE TABLE IF NOT EXISTS project_summaries (
    project_summary_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id             INTEGER NOT NULL,
    project_key         INTEGER NOT NULL,
    project_type        TEXT,
    project_mode        TEXT,
    summary_json        TEXT NOT NULL,
    created_at          TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    manual_start_date   TEXT,  -- Manual override for start date (ISO format YYYY-MM-DD)
    manual_end_date     TEXT,  -- Manual override for end date (ISO format YYYY-MM-DD)
    UNIQUE(user_id, project_key),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS project_skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    level TEXT NOT NULL,
    score REAL NOT NULL,
    evidence_json TEXT,
    UNIQUE(user_id, project_key, skill_name),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

-- USER FILE CONTRIBUTIONS (for collaborative projects)
-- Tracks which files each user worked on, used to filter skill detection

CREATE TABLE IF NOT EXISTS user_code_contributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    file_path TEXT NOT NULL,
    lines_changed INTEGER DEFAULT 0,  -- additions + deletions
    commits_count INTEGER DEFAULT 0,
    recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, project_key, file_path),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_user_code_contributions_user_project
    ON user_code_contributions (user_id, project_key);

CREATE TABLE IF NOT EXISTS github_collaboration_profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    profile_json TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),

    UNIQUE (user_id, project_key, repo_owner, repo_name),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_collaboration_profiles_lookup
    ON github_collaboration_profiles (user_id, project_key, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_issues (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    issue_title TEXT,
    issue_body TEXT,
    labels_json TEXT,
    created_at TEXT,
    closed_at TEXT,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_issues_lookup
    ON github_issues(user_id, project_key, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_issue_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    issue_number INTEGER NOT NULL,
    comment_body TEXT,
    created_at TEXT,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_issue_comments_lookup
    ON github_issue_comments(user_id, project_key, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_pull_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
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
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_prs_lookup
    ON github_pull_requests(user_id, project_key, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_commit_timestamps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    commit_timestamp TEXT NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_commit_timestamps_lookup
    ON github_commit_timestamps(user_id, project_key, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_pr_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    review_json TEXT NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_pr_reviews_lookup
    ON github_pr_reviews(user_id, project_key, repo_owner, repo_name);

CREATE TABLE IF NOT EXISTS github_pr_review_comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    repo_owner TEXT NOT NULL,
    repo_name TEXT NOT NULL,
    pr_number INTEGER NOT NULL,
    comment_json TEXT NOT NULL,
    synced_at TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_github_pr_review_comments_lookup
    ON github_pr_review_comments(user_id, project_key, repo_owner, repo_name);


-- TEXT ACTIVITY TYPE CONTRIBUTION DATA

CREATE TABLE IF NOT EXISTS text_activity_contribution (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    version_key INTEGER UNIQUE NOT NULL,
    start_date TEXT,
    end_date TEXT,
    duration_days INTEGER,
    total_files INTEGER,
    classified_files INTEGER,
    activity_classification_json TEXT,  
    timeline_json TEXT,               
    activity_counts_json TEXT,     
    generated_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (version_key) REFERENCES project_versions(version_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_text_activity_contribution_lookup
    ON text_activity_contribution(version_key);

-- Code activity metrics (per user, project, scope, and source)
CREATE TABLE IF NOT EXISTS code_activity_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,     -- who + which project
    project_key  INTEGER NOT NULL,
    scope        TEXT    NOT NULL,  -- 'individual' or 'collaborative'
    source       TEXT    NOT NULL,  -- where this metric comes from: 'files', 'prs', or 'combined'
    activity_type TEXT   NOT NULL,  -- 'feature_coding', 'refactoring', 'debugging', 'testing', 'documentation'
    event_count  INTEGER NOT NULL,
    total_events INTEGER NOT NULL,
    percent      REAL    NOT NULL,  -- 0–100
    recorded_at  TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_code_activity_metrics_lookup
    ON code_activity_metrics (user_id, project_key, scope, source);

-- Code Collaborative Metrics (pure numeric metrics)
CREATE TABLE IF NOT EXISTS code_collaborative_metrics (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    project_key     INTEGER NOT NULL,
    repo_path       TEXT    NOT NULL,
    -- totals
    commits_all     INTEGER,
    commits_yours   INTEGER,
    commits_coauth  INTEGER,    -- commits where the user is co-author
    merges          INTEGER,
    -- LOC (lines of code)
    loc_added       INTEGER,
    loc_deleted     INTEGER,
    loc_net         INTEGER,    -- net LOC added (add - delete)
    files_touched   INTEGER,    -- number of file-change events
    new_files       INTEGER,    -- number of new files created
    renames         INTEGER,
    -- history
    first_commit_at TEXT,
    last_commit_at  TEXT,
    commits_L30     INTEGER,    -- commits by user in last 30 days
    commits_L90     INTEGER,
    commits_L365    INTEGER,
    longest_streak  INTEGER,
    current_streak  INTEGER,
    top_days        TEXT,
    top_hours       TEXT,
    -- focus
    languages_json  TEXT,
    folders_json    TEXT,   -- top folders by activity
    top_files_json  TEXT,   -- most edited files
    frameworks_json TEXT,
    -- others
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE(user_id, project_key),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_code_collab_metrics_user_project
    ON code_collaborative_metrics (user_id, project_key);

-- Summaries for collaborative code contributions (non-llm or llm)
CREATE TABLE IF NOT EXISTS code_collaborative_summary (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    metrics_id      INTEGER NOT NULL,    -- FK to code_collaborative_metrics.id
    user_id         INTEGER NOT NULL,
    project_key     INTEGER NOT NULL,
    summary_type    TEXT    NOT NULL,    -- 'llm' or 'non-llm'
    content         TEXT    NOT NULL,    -- full manually-written or LLM summaries (project+contribution)
    created_at      TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (metrics_id) REFERENCES code_collaborative_metrics(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_code_collab_summary_user_project
    ON code_collaborative_summary (user_id, project_key);

-- Resume snapshots (frozen resume outputs)
CREATE TABLE IF NOT EXISTS resume_snapshots (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL,
    name          TEXT    NOT NULL,
    resume_json   TEXT    NOT NULL,
    rendered_text TEXT,
    created_at    TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_resume_snapshots_user
    ON resume_snapshots (user_id, created_at);

-- PROJECT FEEDBACK (unmet criteria)
CREATE TABLE IF NOT EXISTS project_feedback (
    feedback_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL,
    project_key     INTEGER NOT NULL,
    project_type    TEXT CHECK (project_type IN ('code','text')),
    skill_name      TEXT NOT NULL,           -- e.g., clarity, structure, OOP, testing_and_ci
    file_name       TEXT NOT NULL DEFAULT '', -- optional: store per-file misses; '' = project-level
    criterion_key   TEXT NOT NULL,           -- stable id, e.g. "clarity.fragments_runons"
    criterion_label TEXT NOT NULL,           -- human-readable title
    expected        TEXT,                    -- what you look for
    observed_json   TEXT,                    -- JSON blob (counts, thresholds, etc.)
    suggestion      TEXT,                    -- how to improve
    generated_at    TEXT NOT NULL DEFAULT (datetime('now')),

    UNIQUE(user_id, project_key, skill_name, file_name, criterion_key),
    FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY(project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_feedback_lookup
    ON project_feedback(user_id, project_key);

CREATE INDEX IF NOT EXISTS idx_project_feedback_skill
    ON project_feedback(user_id, project_key, skill_name);

CREATE TABLE IF NOT EXISTS project_rankings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    project_key INTEGER NOT NULL,
    manual_rank INTEGER, 
    updated_at TEXT DEFAULT (datetime('now')),

    UNIQUE(user_id, project_key),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_project_rankings_user
    ON project_rankings(user_id, project_key, manual_rank);

CREATE TABLE IF NOT EXISTS uploads (
  upload_id   INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id     INTEGER NOT NULL,
  zip_name    TEXT,
  zip_path    TEXT,
  status      TEXT NOT NULL DEFAULT 'started'
              CHECK(status IN ('started','parsed','needs_dedup','needs_classification','needs_project_types','needs_file_roles','needs_summaries','analyzing','done','failed')),
  state_json  TEXT, 
  created_at  TEXT DEFAULT CURRENT_TIMESTAMP,
  updated_at  TEXT DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_uploads_user_time
  ON uploads(user_id, created_at);

CREATE TABLE IF NOT EXISTS project_thumbnails (
    thumbnail_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id      INTEGER NOT NULL,
    project_key  INTEGER NOT NULL,
    image_path   TEXT NOT NULL,
    added_at     TEXT NOT NULL,
    updated_at   TEXT NOT NULL,
    UNIQUE(user_id, project_key),
    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (project_key) REFERENCES projects(project_key) ON DELETE CASCADE

);
