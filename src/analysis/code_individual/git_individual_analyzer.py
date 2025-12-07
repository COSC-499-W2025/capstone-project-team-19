"""
Git Individual Project Analyzer

Analyzes git repositories in individual projects to extract:
- Commit statistics (total commits, average commits per period)
- Timeline of lines added/deleted with timestamps
- Weekly aggregation of code changes
- Activity frequency timeline
- Commit summaries and patterns

This is different from collaborative analysis - focuses on overall repository
health and activity patterns rather than individual contributor metrics.
"""

import os
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict, Counter
import pandas as pd
from src.utils.helpers import is_git_repo
from src.integrations.github.github_oauth import github_oauth
from src.integrations.github.token_store import get_github_token
from src.integrations.github.link_repo import ensure_repo_link, select_and_store_repo
from pathlib import Path
try:
    from src import constants
except ModuleNotFoundError:
    import constants

def analyze_git_individual_project(conn, user_id: int, project_name: str, zip_path: str) -> Dict:
    """
    Analyze git repository for an individual project.

    Returns comprehensive git metrics including:
    - Commit statistics
    - Timeline analysis
    - Weekly code changes
    - Activity patterns
    """

    # Figure out where this zip was extracted under zip_data
    repo_root = Path(__file__).resolve().parents[1]  # .../src/analysis
    zip_data_dir = repo_root / "zip_data"

    zip_name = Path(zip_path).stem  # e.g. real_test4 from ../real_test4.zip

    # Possible base roots where project folders might live:
    #   zip_data/zip_name/zip_name/...
    #   zip_data/zip_name/...
    base_roots = [
        zip_data_dir / zip_name / zip_name,
        zip_data_dir / zip_name,
    ]

    if constants.VERBOSE:
        print("\n" + "=" * 80)
        print(f"[debug] project={project_name}")
        print(f"[debug] zip_path arg={zip_path}")
        for base in base_roots:
            print(f"[debug] base_root candidate={base} (exists? {base.exists()})")

    # Candidate locations for this project's repo
    candidate_roots: List[Path] = []
    for base in base_roots:
        candidate_roots.extend([
            base / project_name,
            base / "individual" / project_name,
            base / "collaborative" / project_name,
        ])

    repo_path: Optional[str] = None
    for root in candidate_roots:
        if constants.VERBOSE:
            print(f"[debug] trying candidate root: {root} (exists? {root.exists()})")
        if root.exists() and is_git_repo(str(root)):
            repo_path = str(root)
            if constants.VERBOSE:
                print(f"[debug] found git repo at: {repo_path}")
            break

    if not repo_path:
        if constants.VERBOSE:
            print("\n" + "=" * 80)
            print(f"No local git repository found for project '{project_name}'")
            print("[debug] Searched under:")
            for root in candidate_roots:
                print(f"  - {root}")
            print("=" * 80)

        # Offer GitHub connection option / gracefully skip
        return _handle_no_git_repo(conn, user_id, project_name)

    if constants.VERBOSE:
        print(f"\n{'='*80}")
        print(f"Analyzing Git Repository for: {project_name}")
        print(f"Repository found at: {repo_path}")
        print(f"{'='*80}\n")

    # Extract git metrics
    commit_stats = get_commit_statistics(repo_path)
    timeline_data = get_lines_timeline(repo_path)
    weekly_changes = calculate_weekly_changes(timeline_data)
    activity_timeline = generate_activity_timeline(timeline_data)

    return {
        "has_git": True,
        "repo_path": repo_path,
        "commit_stats": commit_stats,
        "timeline_data": timeline_data,
        "weekly_changes": weekly_changes,
        "activity_timeline": activity_timeline,
    }


def _handle_no_git_repo(conn, user_id: int, project_name: str) -> Optional[Dict]:
    """
    Handle case when no local git repository is found.
    Offers to connect to GitHub to link a remote repository.
    """
    token = get_github_token(conn, user_id)

    # User has token already, allow linking without re-authentication
    if token:
        print(f"\nNo local .git found for {project_name}, but you're already logged into GitHub.")

        # Check if repo is already linked
        if ensure_repo_link(conn, user_id, project_name, token):
            print(f"[info] GitHub repo already linked for {project_name}")
            print("[info] However, git analysis requires a local clone with .git directory.")
            return None

        # Offer to link repo
        ans = input("\nWould you like to link this project to a GitHub repository? (y/n): ").strip().lower()
        if ans in {"y", "yes"}:
            select_and_store_repo(conn, user_id, project_name, token)
            print("\n[info] Repository linked, but git analysis requires a local clone.")
            print("[tip] Upload a zip file that includes the .git directory for full analysis.")

        return None

    # No token - offer GitHub authentication
    print("\n[info] Git analysis requires access to git history.")
    ans = input(
        f"\nConnect to GitHub to link {project_name} to a remote repository? (y/n): "
    ).strip().lower()

    if ans in {"y", "yes"}:
        token = github_oauth(conn, user_id)
        select_and_store_repo(conn, user_id, project_name, token)
        print("\n[info] Repository linked, but git analysis requires a local clone.")
        print("[tip] Upload a zip file that includes the .git directory for full analysis.")
    else:
        print(f"\n[skip] Skipping git analysis for {project_name}")

    return None


def get_commit_statistics(repo_path: str) -> Dict:
    """
    Get comprehensive commit statistics for the repository.

    Returns:
    - total_commits: Total number of commits
    - first_commit_date: Date of first commit
    - last_commit_date: Date of last commit
    - average_commits_per_week: Average commits per week
    - average_commits_per_month: Average commits per month
    - unique_authors: Number of unique authors
    - commit_messages: List of commit messages with dates
    """

    try:
        # Get total commit count
        result = subprocess.run(
            ['git', '-C', repo_path, 'rev-list', '--count', '--no-merges','HEAD'],
            capture_output=True,
            text=True,
            timeout=30
        )

        total_commits = int(result.stdout.strip()) if result.returncode == 0 else 0

        # Get first and last commit dates
        first_commit_result = subprocess.run(
            ['git', '-C', repo_path, 'log', '--reverse', '--format=%ai', '--no-merges'],
            capture_output=True,
            text=True,
            timeout=30
        )

        last_commit_result = subprocess.run(
            ['git', '-C', repo_path, 'log', '--format=%ai', '--no-merges', '--max-count=1'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Get first line from reversed output for first commit
        first_commit_date = None
        if first_commit_result.returncode == 0 and first_commit_result.stdout.strip():
            first_commit_date = first_commit_result.stdout.strip().split('\n')[0]

        last_commit_date = last_commit_result.stdout.strip() if last_commit_result.returncode == 0 else None

        # Calculate time span
        time_span_days = 0
        if first_commit_date and last_commit_date:
            first_dt = datetime.fromisoformat(first_commit_date.split()[0])
            last_dt = datetime.fromisoformat(last_commit_date.split()[0])
            time_span_days = (last_dt - first_dt).days

        # Calculate averages
        time_span_weeks = max(time_span_days / 7, 1)
        time_span_months = max(time_span_days / 30, 1)

        avg_commits_per_week = total_commits / time_span_weeks if time_span_weeks > 0 else 0
        avg_commits_per_month = total_commits / time_span_months if time_span_months > 0 else 0

        # Get unique authors
        authors_result = subprocess.run(
            ['git', '-C', repo_path, 'log', '--format=%an','--no-merges'],
            capture_output=True,
            text=True,
            timeout=30
        )

        unique_authors = len(set(authors_result.stdout.strip().split('\n'))) if authors_result.returncode == 0 else 0

        # Get recent commit messages (last 10)
        messages_result = subprocess.run(
            ['git', '-C', repo_path, 'log', '--format=%ai|%s', '--no-merges','--max-count=10'],
            capture_output=True,
            text=True,
            timeout=30
        )

        commit_messages = []
        if messages_result.returncode == 0:
            for line in messages_result.stdout.strip().split('\n'):
                if '|' in line:
                    date, message = line.split('|', 1)
                    commit_messages.append({'date': date, 'message': message})

        return {
            'total_commits': total_commits,
            'first_commit_date': first_commit_date,
            'last_commit_date': last_commit_date,
            'time_span_days': time_span_days,
            'average_commits_per_week': round(avg_commits_per_week, 2),
            'average_commits_per_month': round(avg_commits_per_month, 2),
            'unique_authors': unique_authors,
            'recent_commits': commit_messages
        }

    except Exception as e:
        print(f"Error getting commit statistics: {e}")
        return {}


def get_lines_timeline(repo_path: str) -> List[Dict]:
    """
    Get timeline of lines added/deleted with timestamps for each commit.

    Returns list of dictionaries with:
    - commit_hash: Short commit hash
    - date: Commit date
    - timestamp: Unix timestamp
    - lines_added: Lines added in this commit
    - lines_deleted: Lines deleted in this commit
    - net_lines: Net change (added - deleted)
    """

    try:
        # Get commit data with numstat (lines added/deleted)
        result = subprocess.run(
            ['git', '-C', repo_path, 'log', '--numstat', '--format=%H|%ai', '--no-merges'],
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode != 0:
            return []

        timeline = []
        current_commit = None
        current_date = None

        for line in result.stdout.strip().split('\n'):
            if '|' in line:
                # Commit line
                parts = line.split('|')
                current_commit = parts[0][:7]  # Short hash
                current_date = parts[1]
            elif line.strip() and current_commit:
                # Numstat line: added    deleted    filename
                parts = line.split('\t')
                if len(parts) >= 3:
                    try:
                        added = int(parts[0]) if parts[0].isdigit() else 0
                        deleted = int(parts[1]) if parts[1].isdigit() else 0

                        # Parse timestamp
                        dt = datetime.fromisoformat(current_date.split()[0])
                        timestamp = int(dt.timestamp())

                        # Find or create entry for this commit
                        existing = next((t for t in timeline if t['commit_hash'] == current_commit), None)

                        if existing:
                            existing['lines_added'] += added
                            existing['lines_deleted'] += deleted
                            existing['net_lines'] = existing['lines_added'] - existing['lines_deleted']
                        else:
                            timeline.append({
                                'commit_hash': current_commit,
                                'date': current_date,
                                'timestamp': timestamp,
                                'lines_added': added,
                                'lines_deleted': deleted,
                                'net_lines': added - deleted
                            })

                    except (ValueError, IndexError):
                        continue

        return sorted(timeline, key=lambda x: x['timestamp'])

    except Exception as e:
        print(f"Error getting lines timeline: {e}")
        return []


def calculate_weekly_changes(timeline_data: List[Dict]) -> Dict:
    """
    Calculate weekly aggregation of additions, deletions, and net lines.

    Returns dictionary with:
    - weeks: List of week start dates
    - additions_per_week: Lines added per week
    - deletions_per_week: Lines deleted per week
    - net_per_week: Net lines per week
    """

    if not timeline_data:
        return {}

    # Convert to DataFrame for easier aggregation
    df = pd.DataFrame(timeline_data)

    if df.empty:
        return {}

    # Convert timestamp to datetime
    df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')

    # Group by week
    df['week_start'] = df['datetime'].dt.to_period('W').dt.start_time

    weekly = df.groupby('week_start').agg({
        'lines_added': 'sum',
        'lines_deleted': 'sum',
        'net_lines': 'sum'
    }).reset_index()

    return {
        'weeks': [str(w.date()) for w in weekly['week_start']],
        'additions_per_week': weekly['lines_added'].tolist(),
        'deletions_per_week': weekly['lines_deleted'].tolist(),
        'net_per_week': weekly['net_lines'].tolist(),
        'total_weeks': len(weekly)
    }


def generate_activity_timeline(timeline_data: List[Dict]) -> Dict:
    """
    Generate activity frequency timeline showing commit patterns.

    Returns:
    - commits_per_day: Dictionary of date -> commit count
    - commits_per_month: Dictionary of month -> commit count
    - busiest_day: Day with most commits
    - busiest_month: Month with most commits
    - activity_summary: Summary statistics
    """

    if not timeline_data:
        return {}

    # Count commits per day
    commits_by_day = defaultdict(int)
    commits_by_month = defaultdict(int)

    for entry in timeline_data:
        dt = datetime.fromtimestamp(entry['timestamp'])
        date_str = dt.strftime('%Y-%m-%d')
        month_str = dt.strftime('%Y-%m')

        commits_by_day[date_str] += 1
        commits_by_month[month_str] += 1

    # Find busiest periods
    busiest_day = max(commits_by_day.items(), key=lambda x: x[1]) if commits_by_day else (None, 0)
    busiest_month = max(commits_by_month.items(), key=lambda x: x[1]) if commits_by_month else (None, 0)

    # Calculate activity patterns
    day_counts = list(commits_by_day.values())
    avg_commits_per_active_day = sum(day_counts) / len(day_counts) if day_counts else 0

    return {
        'commits_per_day': dict(commits_by_day),
        'commits_per_month': dict(commits_by_month),
        'busiest_day': {'date': busiest_day[0], 'commits': busiest_day[1]},
        'busiest_month': {'month': busiest_month[0], 'commits': busiest_month[1]},
        'total_active_days': len(commits_by_day),
        'total_active_months': len(commits_by_month),
        'average_commits_per_active_day': round(avg_commits_per_active_day, 2)
    }


def display_git_results(git_data: Dict) -> None:
    """
    Display git analysis results in a readable, actionable format.
    """

    if not git_data.get('has_git'):
        print("No git repository found for this project.")
        return

    print(f"\n{'='*80}")
    print("GIT REPOSITORY ANALYSIS")
    print(f"{'='*80}\n")

    # Commit statistics
    commit_stats = git_data.get('commit_stats', {})
    if commit_stats:
        print("OVERVIEW:")
        print(f"  Total Commits: {commit_stats.get('total_commits', 0)}")
        print(f"  Time Span: {commit_stats.get('time_span_days', 0)} days")
        print(f"  First Commit: {commit_stats.get('first_commit_date', 'N/A')[:10]}")
        print(f"  Last Commit: {commit_stats.get('last_commit_date', 'N/A')[:10]}")
        print()

        print("COMMIT FREQUENCY:")
        print(f"  Average per Week: {commit_stats.get('average_commits_per_week', 0):.2f}")
        print(f"  Average per Month: {commit_stats.get('average_commits_per_month', 0):.2f}")
        print()

    # Weekly changes
    weekly = git_data.get('weekly_changes', {})
    if weekly and weekly.get('weeks'):
        total_additions = sum(weekly.get('additions_per_week', []))
        total_deletions = sum(weekly.get('deletions_per_week', []))
        total_net = sum(weekly.get('net_per_week', []))

        print("CODE CHANGE SUMMARY:")
        print(f"  Total Weeks Active: {weekly.get('total_weeks', 0)}")
        print(f"  Total Lines Added: {total_additions:,}")
        print(f"  Total Lines Deleted: {total_deletions:,}")
        print(f"  Net Lines Changed: {total_net:+,}")
        print()

        # Show last 5 weeks
        weeks = weekly.get('weeks', [])
        additions = weekly.get('additions_per_week', [])
        deletions = weekly.get('deletions_per_week', [])
        net = weekly.get('net_per_week', [])

        if len(weeks) > 0:
            print("RECENT WEEKLY ACTIVITY:")
            start_idx = max(0, len(weeks) - 5)
            for i in range(start_idx, len(weeks)):
                print(f"Week of {weeks[i]}: +{additions[i]:,} -{deletions[i]:,} (net: {net[i]:+,})")
            print()

    # Activity timeline
    activity = git_data.get('activity_timeline', {})
    if activity:
        print("ACTIVITY PATTERNS:")
        print(f"  Total Active Days: {activity.get('total_active_days', 0)}")
        print(f"  Total Active Months: {activity.get('total_active_months', 0)}")
        print(f"  Avg Commits per Active Day: {activity.get('average_commits_per_active_day', 0):.2f}")

        busiest_day = activity.get('busiest_day', {})
        busiest_month = activity.get('busiest_month', {})

        if busiest_day.get('date'):
            print(f"Day with most commits: {busiest_day['date']} ({busiest_day['commits']} commits)")

        if busiest_month.get('month'):
            print(f"Month with most commits: {busiest_month['month']} ({busiest_month['commits']} commits)")
        print()

    # Recent commits
    recent = commit_stats.get('recent_commits', [])
    if recent:
        print("RECENT COMMITS:")
        for i, commit in enumerate(recent[:5], 1):
            date = commit['date'][:10]
            message = commit['message'][:70] + ('...' if len(commit['message']) > 70 else '')
            print(f"  {i}. {date} - {message}")
        print()

    print(f"{'='*80}\n")
