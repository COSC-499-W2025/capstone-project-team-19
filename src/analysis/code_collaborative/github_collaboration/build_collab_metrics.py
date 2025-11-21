"""
Converts the raw GitHub API JSON from fetch_github_metrics() into the RawUserCollabMetrics + RawTeamCollabMetrics objects expected by the collaboration-skill pipeline.
"""
from datetime import datetime
from src.integrations.github.github_analysis import fetch_github_metrics
from src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile import compute_collaboration_profile
from .models import RawUserCollabMetrics, RawTeamCollabMetrics

def build_collaboration_metrics(token, owner, repo, username):
    raw_metrics = fetch_github_metrics(token, owner, repo, username)

    commits_daily = raw_metrics["commits"]
    issues = raw_metrics["issues"]
    prs = raw_metrics["pull_requests"]
    contributions = raw_metrics["contributions"]
    commit_timestamps = raw_metrics["commit_timestamps"]
    review_data = raw_metrics.get("reviews", {})

    commits = sum(commits_daily.values())
    prs_opened = prs["total_opened"]
    prs_reviewed = sum(
        len(pr_review_data.get("reviews", []))
        for pr_review_data in review_data.values()
    )
    issues_opened = issues["total_opened"]
    issue_comments = len(issues["user_issue_comments"])

    pr_timestamps = [
        datetime.fromisoformat(pr["created_at"])
        for pr in prs["user_prs"]
        if pr.get("created_at")
    ]

    review_timestamps = []
    review_comments = []

    for pr_number, pr_review_data in review_data.items():
        for review in pr_review_data.get("reviews", []):
            timestamp = review.get("submitted_at")
            if timestamp:
                review_timestamps.append(datetime.fromisoformat(timestamp.replace("Z", "")))

        for comment in pr_review_data.get("review_comments", []):
            review_comments.append(comment.get("body", ""))

    team_total_commits = contributions["team"]["total_commits"]
    team_total_prs = prs["total_opened"] # team-wide PRs if needed
    team_total_reviews = sum(
        len(pr_rev.get("reviews", []))
        for pr_rev in review_data.values()
    )
    team_total_issues = issues["total_opened"]
    team_total_additions = contributions["team"]["total_additions"]
    team_total_deletions = contributions["team"]["total_deletions"]

    user = RawUserCollabMetrics(
        commits=commits,
        prs_opened=prs_opened,
        prs_reviewed=prs_reviewed,
        issues_opened=issues_opened,
        issue_comments=issue_comments,
        review_comments=review_comments,

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
        total_additions=team_total_additions,
        total_deletions=team_total_deletions,
    )

    return user, team

def run_collaboration_analysis(token, owner, repo, username):
    user, team = build_collaboration_metrics(token, owner, repo, username)
    return compute_collaboration_profile(user, team)