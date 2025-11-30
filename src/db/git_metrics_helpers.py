def extract_git_metrics(git_data):
    """
    Extract git metrics from git_data dictionary into a tuple for database storage.
    """
    commit_stats = git_data.get('commit_stats', {})
    weekly_changes = git_data.get('weekly_changes', {})
    activity_timeline = git_data.get('activity_timeline', {})

    # Calculate totals from weekly changes
    total_lines_added = sum(weekly_changes.get('additions_per_week', []))
    total_lines_deleted = sum(weekly_changes.get('deletions_per_week', []))
    net_lines_changed = sum(weekly_changes.get('net_per_week', []))

    # Extract activity patterns
    busiest_day = activity_timeline.get('busiest_day', {})
    busiest_month = activity_timeline.get('busiest_month', {})

    return (
        commit_stats.get('total_commits'),
        commit_stats.get('first_commit_date'),
        commit_stats.get('last_commit_date'),
        commit_stats.get('time_span_days'),
        commit_stats.get('average_commits_per_week'),
        commit_stats.get('average_commits_per_month'),
        commit_stats.get('unique_authors'),
        total_lines_added,
        total_lines_deleted,
        net_lines_changed,
        weekly_changes.get('total_weeks'),
        activity_timeline.get('total_active_days'),
        activity_timeline.get('total_active_months'),
        activity_timeline.get('average_commits_per_active_day'),
        busiest_day.get('date'),
        busiest_day.get('commits'),
        busiest_month.get('month'),
        busiest_month.get('commits')
    )
