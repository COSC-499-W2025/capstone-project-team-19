from src.analysis.code_collaborative.github_collaboration.participation import compute_participation
from src.analysis.code_collaborative.github_collaboration.models import RawUserCollabMetrics
import datetime


def make_user(prs, reviews, issues, comments, review_comments):
    return RawUserCollabMetrics(
        commits=0,
        prs_opened=prs,
        prs_reviewed=reviews,
        issues_opened=issues,
        issue_comments=comments,
        review_comments=review_comments,
        additions=0,
        deletions=0,
        commit_timestamps=[],
        pr_timestamps=[],
        review_timestamps=[],
    )


def test_participation_no_activity():
    user = make_user(0, 0, 0, 0, [])
    result = compute_participation(user)

    assert result["channels_used"] == 0
    assert result["activity_score"] == 0


def test_participation_single_channel_each():
    # prs_opened only
    u1 = make_user(1, 0, 0, 0, [])
    r1 = compute_participation(u1)
    assert r1["channels_used"] == 1
    assert r1["activity_score"] == 1 * 1.2

    # prs_reviewed only
    u2 = make_user(0, 2, 0, 0, [])
    r2 = compute_participation(u2)
    assert r2["channels_used"] == 1
    assert r2["activity_score"] == 2 * 1.0

    # issues_opened only
    u3 = make_user(0, 0, 3, 0, [])
    r3 = compute_participation(u3)
    assert r3["channels_used"] == 1
    assert r3["activity_score"] == 3 * 1.3

    # issue_comments only
    u4 = make_user(0, 0, 0, 4, [])
    r4 = compute_participation(u4)
    assert r4["channels_used"] == 1
    assert r4["activity_score"] == 4 * 0.7

    # review_comments only
    u5 = make_user(0, 0, 0, 0, ["a"])
    r5 = compute_participation(u5)
    assert r5["channels_used"] == 1
    assert r5["activity_score"] == 0  # comments don't affect score


def test_participation_multiple_channels():
    user = make_user(
        prs=2,            # >0 → channel
        reviews=1,        # >0 → channel
        issues=0,         # no channel
        comments=3,       # >0 → channel
        review_comments=["nice"],  # >0 → channel
    )

    # channels: prs_opened, prs_reviewed, issue_comments, review_comments
    result = compute_participation(user)
    assert result["channels_used"] == 4

    # activity score = (prs*1.2) + (reviews*1.0) + (comments*0.7)
    expected_score = (2 * 1.2) + (1 * 1.0) + (3 * 0.7)
    assert result["activity_score"] == expected_score
