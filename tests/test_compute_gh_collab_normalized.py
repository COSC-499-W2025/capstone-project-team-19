from src.analysis.code_collaborative.github_collaboration.normalized import compute_normalized_contribution
from src.analysis.code_collaborative.github_collaboration.models import RawUserCollabMetrics, RawTeamCollabMetrics
import datetime


def make_user(commits, prs, reviews, issues, adds, dels):
    return RawUserCollabMetrics(
        commits=commits,
        prs_opened=prs,
        prs_reviewed=reviews,
        issues_opened=issues,
        issue_comments=0,
        pr_discussion_comments=0,
        review_comments=[],
        additions=adds,
        deletions=dels,
        commit_timestamps=[],
        pr_timestamps=[],
        review_timestamps=[],
    )


def make_team(commits, prs, reviews, issues, adds, dels):
    return RawTeamCollabMetrics(
        total_commits=commits,
        total_prs=prs,
        total_reviews=reviews,
        total_issues=issues,
        total_issue_comments=0,
        total_pr_discussion_comments=0,
        total_review_comments=0,
        total_additions=adds,
        total_deletions=dels,
    )


def test_normalized_basic():
    user = make_user(10, 4, 6, 2, 100, 40)
    team = make_team(50, 20, 30, 10, 500, 200)

    result = compute_normalized_contribution(user, team)

    assert result["commit_share"] == 10 / 50
    assert result["pr_share"] == 4 / 20
    assert result["review_share"] == 6 / 30
    assert result["issue_share"] == 2 / 10
    assert result["addition_share"] == 100 / 500
    assert result["deletion_share"] == 40 / 200

    # dominant activity = highest % among commits/prs/reviews/issues
    expected_dom = max(
        {
            "commits": 10 / 50,
            "prs": 4 / 20,
            "reviews": 6 / 30,
            "issues": 2 / 10,
        },
        key=lambda k: {
            "commits": 10 / 50,
            "prs": 4 / 20,
            "reviews": 6 / 30,
            "issues": 2 / 10,
        }[k]
    )
    assert result["dominant_activity"] == expected_dom

    assert result["total_behavior_score"] == (
        10/50 + 4/20 + 6/30 + 2/10
    )


def test_normalized_divide_by_zero():
    user = make_user(5, 3, 2, 1, 10, 4)
    team = make_team(0, 0, 0, 0, 0, 0)

    result = compute_normalized_contribution(user, team)

    # all ratios go to zero, no crash
    assert result["commit_share"] == 0
    assert result["pr_share"] == 0
    assert result["review_share"] == 0
    assert result["issue_share"] == 0
    assert result["addition_share"] == 0
    assert result["deletion_share"] == 0

    # dominant_activity still returned, all equal → first one in list (“commits”)
    assert result["dominant_activity"] == "commits"

    assert result["total_behavior_score"] == 0


def test_normalized_dominant_activity_changes():
    user = make_user(commits=1, prs=10, reviews=0, issues=0, adds=0, dels=0)
    team = make_team(commits=100, prs=20, reviews=100, issues=100, adds=1, dels=1)

    result = compute_normalized_contribution(user, team)

    # prs_opened / total_prs = 10/20 = 0.5 → highest
    assert result["dominant_activity"] == "prs"
