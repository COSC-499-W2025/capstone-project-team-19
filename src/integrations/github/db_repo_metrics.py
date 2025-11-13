import json

# store the metrics retrieved from GitHub (via GitHub REST API) in the local db
def store_github_repo_metrics(conn, user_id, project_name, owner, repo, metrics):
    metrics_json = json.dumps(metrics)

    conn.execute("""
        INSERT INTO github_repo_metrics (
            user_id, project_name, repo_owner, repo_name, metrics_json
        )
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id, project_name, repo_owner, repo_name)
        DO UPDATE SET metrics_json = excluded.metrics_json
    """, (user_id, project_name, owner, repo, metrics_json))

    conn.commit()

# get a github repositories metrics from the local db
def get_github_repo_metrics(conn, user_id, project_name, owner, repo):
    row = conn.execute("""
        SELECT metrics_json 
        FROM github_repo_metrics
        WHERE user_id=? AND project_name=? AND repo_owner=? AND repo_name=?
        LIMIT 1
    """, (user_id, project_name, owner, repo)).fetchone()

    if not row: return None

    return json.loads(row[0])