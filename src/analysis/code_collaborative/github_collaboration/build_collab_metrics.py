"""
Converts the raw GitHub API JSON from fetch_github_metrics() into the RawUserCollabMetrics + RawTeamCollabMetrics objects expected by the collaboration-skill pipeline.
"""
from datetime import datetime
from src.integrations.github.github_analysis import fetch_github_metrics
from src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile import compute_collaboration_profile, compute_skill_levels
from .models import RawUserCollabMetrics, RawTeamCollabMetrics

def build_collaboration_metrics(token, owner, repo, username):
    raw_metrics = fetch_github_metrics(token, owner, repo, username)

    # ===== REST METRICS =====
    commits_daily = raw_metrics["commits"]
    issues = raw_metrics["issues"]
    contributions = raw_metrics["contributions"]
    commit_timestamps = raw_metrics["commit_timestamps"]

    # ===== GRAPHQL METRICS =====
    pr_data = raw_metrics["graphql_prs"]

    # ======================
    # USER METRICS
    # ======================

    commits = sum(commits_daily.values())
    # user issues must come from the list
    user_issues = issues.get("user_issues", [])
    issues_opened = len(user_issues)

    # user issue comments must always be a list
    issue_comments = issues.get("user_issue_comments", [])
    if isinstance(issue_comments, int):
        issue_comments = []
    issue_comments_count = len(issue_comments)

    user_prs = pr_data.get("user_prs", [])
    prs_opened = len(user_prs)
    prs_reviewed = pr_data.get("prs_reviewed", 0)

    review_comments_bodies = pr_data.get("review_comments", [])
    user_pr_discussion_comments = pr_data.get("user_pr_discussion_comments", [])
    if isinstance(user_pr_discussion_comments, int):
        user_pr_discussion_comments = []

    review_timestamps = [
        datetime.fromisoformat(ts.replace("Z", ""))
        for ts in pr_data.get("review_timestamps", [])
        if isinstance(ts, str)
    ]

    pr_timestamps = [
        datetime.fromisoformat(ts.replace("Z", ""))
        for ts in pr_data.get("pr_timestamps", [])
        if isinstance(ts, str)
    ]

    # ======================
    # TEAM METRICS
    # ======================

    team_total_commits = contributions["team"]["total_commits"]
    team_total_prs = pr_data["team_total_prs"]
    team_total_reviews = pr_data.get("team_total_reviews", 0)
    team_total_issues = issues["total_opened"]

    team_total_issue_comments = issues.get("total_issue_comments", 0)
    team_total_pr_discussion_comments = pr_data.get("team_pr_discussion_comments", 0)
    team_total_review_comments = len(pr_data.get("review_comments", []))

    team_total_additions = contributions["team"]["total_additions"]
    team_total_deletions = contributions["team"]["total_deletions"]

    # ======================
    # BUILD OBJECTS
    # ======================

    user = RawUserCollabMetrics(
        commits=commits,
        prs_opened=prs_opened,
        prs_reviewed=prs_reviewed,
        issues_opened=issues_opened,

        issue_comments=issue_comments_count,
        pr_discussion_comments=len(user_pr_discussion_comments),
        review_comments=review_comments_bodies,

        additions=contributions["user"]["additions"],
        deletions=contributions["user"]["deletions"],

        commit_timestamps=commit_timestamps,
        pr_timestamps=pr_timestamps,
        review_timestamps=review_timestamps,
    )

    team = RawTeamCollabMetrics(
        total_commits=team_total_commits,
        total_prs=team_total_prs,
        total_reviews=team_total_reviews,
        total_issues=team_total_issues,

        total_issue_comments=team_total_issue_comments,
        total_pr_discussion_comments=team_total_pr_discussion_comments,
        total_review_comments=team_total_review_comments,

        total_additions=team_total_additions,
        total_deletions=team_total_deletions,
    )

    return user, team

def run_collaboration_analysis(token, owner, repo, username):
    user, team = build_collaboration_metrics(
        token,
        owner,
        repo,
        username
    )

    profile = compute_collaboration_profile(user, team)
    profile["skill_levels"] = compute_skill_levels(profile)

    return profile