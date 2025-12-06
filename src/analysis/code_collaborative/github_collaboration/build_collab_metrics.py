"""
Converts the raw GitHub API JSON from fetch_github_metrics() into the RawUserCollabMetrics + RawTeamCollabMetrics objects expected by the collaboration-skill pipeline.
"""
from datetime import datetime
from src.integrations.github.github_analysis import fetch_github_metrics
from src.analysis.code_collaborative.github_collaboration.compute_gh_collaboration_profile import compute_collaboration_profile, compute_skill_levels
from .models import RawUserCollabMetrics, RawTeamCollabMetrics

def build_collaboration_metrics(token, owner, repo, username):
    raw_metrics = fetch_github_metrics(token, owner, repo, username)

    commits_daily = raw_metrics["commits"]
    issues = raw_metrics["issues"]
    prs = raw_metrics["pull_requests"]
    contributions = raw_metrics["contributions"]
    commit_timestamps = raw_metrics["commit_timestamps"]
    review_data = raw_metrics.get("reviews", {})
    pr_discussion = raw_metrics.get("pr_discussion_comments", {})

    # === user counts ===

    commits = sum(commits_daily.values()) # commits authored by user
    prs_opened = prs["total_opened"] # PRs the user opened
    issues_opened = issues["total_opened"] # issues the user opened
    issue_comments = issues.get("user_issue_comments", 0) # issue comments by user (already filtered in issues["user_issue_comments"])

    # PR discussion comments by user
    user_pr_discussion_comments = sum(
        1 for c in pr_discussion
        if c.get("user", {}).get("login") == username
    )

    # Review events + review timestamps + review comments written by user
    prs_reviewed = 0
    review_timestamps = []
    review_comments_bodies = []

    for pr_number, pr_review_data in review_data.items():
        # review events (approve / request changes / comment)
        for review in pr_review_data.get("reviews", []):
            author = review.get("user", {}).get("login")
            ts = review.get("submitted_at")

            if author == username:
                prs_reviewed += 1

            if ts:
                review_timestamps.append(
                    datetime.fromisoformat(ts.replace("Z", ""))
                )    

        # inline review comments
        for comment in pr_review_data.get("review_comments", []):
            body = (comment.get("body") or "").strip()
            if not body:
                continue

            author = comment.get("user", {}).get("login")
            if author == username:
                review_comments_bodies.append(body)

    # timestamps for PRs opened by user
    pr_timestamps = [
        datetime.fromisoformat(pr["created_at"])
        for pr in prs["user_prs"]
        if pr.get("created_at")
    ]

    # === team totals ===
    team_total_commits = contributions["team"]["total_commits"]
    team_total_prs = prs["total_opened"]  # repo-wide PR count from get_gh_repo_prs
    team_total_reviews = sum(
        len(pr_rev.get("reviews", [])) for pr_rev in review_data.values()
    )
    team_total_issues = issues["total_opened"]
    team_total_additions = contributions["team"]["total_additions"]
    team_total_deletions = contributions["team"]["total_deletions"]

    # team-wide issue comments (you will add this in get_gh_repo_issues)
    team_total_issue_comments = issues.get("total_issue_comments", 0)

    # team-wide PR discussion comments
    team_total_pr_discussion_comments = len(pr_discussion)

    # team-wide inline review comments
    team_total_review_comments = sum(
        len(pr_rev.get("review_comments", []))
        for pr_rev in review_data.values()
    )    

    # === build user / team objects ===

    user = RawUserCollabMetrics(
        commits=commits,
        prs_opened=prs_opened,
        prs_reviewed=prs_reviewed,
        issues_opened=issues_opened,
        issue_comments=issue_comments,
        pr_discussion_comments=user_pr_discussion_comments,
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
    user, team = build_collaboration_metrics(token, owner, repo, username)
    profile = compute_collaboration_profile(user, team)

    skill_levels = compute_skill_levels(profile)
    profile["skill_levels"] = skill_levels

    return profile