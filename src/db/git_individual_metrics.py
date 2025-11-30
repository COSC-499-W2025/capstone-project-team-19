"""
Database functions for storing and retrieving git individual metrics.
"""

def git_individual_metrics_exists(conn, user_id, project_name):
    """
    Check if git individual metrics already exist for a project.
    """
    cur = conn.execute("""
        SELECT 1 FROM git_individual_metrics
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name))

    return cur.fetchone() is not None


def insert_git_individual_metrics(
    conn,
    user_id,
    project_name,
    total_commits,
    first_commit_date,
    last_commit_date,
    time_span_days,
    average_commits_per_week,
    average_commits_per_month,
    unique_authors,
    total_lines_added,
    total_lines_deleted,
    net_lines_changed,
    total_weeks_active,
    total_active_days,
    total_active_months,
    average_commits_per_active_day,
    busiest_day,
    busiest_day_commits,
    busiest_month,
    busiest_month_commits
):
    """
    Insert git individual metrics into the database.
    """
    conn.execute("""
        INSERT INTO git_individual_metrics (
            user_id, project_name,
            total_commits, first_commit_date, last_commit_date, time_span_days,
            average_commits_per_week, average_commits_per_month, unique_authors,
            total_lines_added, total_lines_deleted, net_lines_changed, total_weeks_active,
            total_active_days, total_active_months, average_commits_per_active_day,
            busiest_day, busiest_day_commits, busiest_month, busiest_month_commits
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id, project_name,
        total_commits, first_commit_date, last_commit_date, time_span_days,
        average_commits_per_week, average_commits_per_month, unique_authors,
        total_lines_added, total_lines_deleted, net_lines_changed, total_weeks_active,
        total_active_days, total_active_months, average_commits_per_active_day,
        busiest_day, busiest_day_commits, busiest_month, busiest_month_commits
    ))
    conn.commit()


def update_git_individual_metrics(
    conn,
    user_id,
    project_name,
    total_commits,
    first_commit_date,
    last_commit_date,
    time_span_days,
    average_commits_per_week,
    average_commits_per_month,
    unique_authors,
    total_lines_added,
    total_lines_deleted,
    net_lines_changed,
    total_weeks_active,
    total_active_days,
    total_active_months,
    average_commits_per_active_day,
    busiest_day,
    busiest_day_commits,
    busiest_month,
    busiest_month_commits
):
    """
    Update existing git individual metrics in the database.
    """
    conn.execute("""
        UPDATE git_individual_metrics SET
            total_commits = ?,
            first_commit_date = ?,
            last_commit_date = ?,
            time_span_days = ?,
            average_commits_per_week = ?,
            average_commits_per_month = ?,
            unique_authors = ?,
            total_lines_added = ?,
            total_lines_deleted = ?,
            net_lines_changed = ?,
            total_weeks_active = ?,
            total_active_days = ?,
            total_active_months = ?,
            average_commits_per_active_day = ?,
            busiest_day = ?,
            busiest_day_commits = ?,
            busiest_month = ?,
            busiest_month_commits = ?,
            last_analyzed = datetime('now')
        WHERE user_id = ? AND project_name = ?
    """, (
        total_commits, first_commit_date, last_commit_date, time_span_days,
        average_commits_per_week, average_commits_per_month, unique_authors,
        total_lines_added, total_lines_deleted, net_lines_changed, total_weeks_active,
        total_active_days, total_active_months, average_commits_per_active_day,
        busiest_day, busiest_day_commits, busiest_month, busiest_month_commits,
        user_id, project_name
    ))
    conn.commit()


def get_git_individual_metrics(conn, user_id, project_name):
    """
    Retrieve stored git individual metrics for a given project.
    """
    cur = conn.execute("""
        SELECT
            total_commits, first_commit_date, last_commit_date, time_span_days,
            average_commits_per_week, average_commits_per_month, unique_authors,
            total_lines_added, total_lines_deleted, net_lines_changed, total_weeks_active,
            total_active_days, total_active_months, average_commits_per_active_day,
            busiest_day, busiest_day_commits, busiest_month, busiest_month_commits,
            last_analyzed
        FROM git_individual_metrics
        WHERE user_id = ? AND project_name = ?
    """, (user_id, project_name))

    row = cur.fetchone()

    if not row:
        return None

    return {
        'total_commits': row[0],
        'first_commit_date': row[1],
        'last_commit_date': row[2],
        'time_span_days': row[3],
        'average_commits_per_week': row[4],
        'average_commits_per_month': row[5],
        'unique_authors': row[6],
        'total_lines_added': row[7],
        'total_lines_deleted': row[8],
        'net_lines_changed': row[9],
        'total_weeks_active': row[10],
        'total_active_days': row[11],
        'total_active_months': row[12],
        'average_commits_per_active_day': row[13],
        'busiest_day': row[14],
        'busiest_day_commits': row[15],
        'busiest_month': row[16],
        'busiest_month_commits': row[17],
        'last_analyzed': row[18]
    }
