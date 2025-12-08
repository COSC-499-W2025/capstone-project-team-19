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
        pr_discussion_comments=0,
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

    # prs_reviewed only (no review comments = low quality = 0.5x weight)
    u2 = make_user(0, 2, 0, 0, [])
    r2 = compute_participation(u2)
    assert r2["channels_used"] == 1
    # With no review comments, quality score is 0, so multiplier is 0.5
    assert r2["activity_score"] == 2 * 0.5

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

    # activity score = (prs*1.2) + (reviews*weight) + (comments*0.7)
    # With only "nice" as review comment, quality is low, so weight is ~0.5
    # For simplicity, we'll just check it's in a reasonable range
    assert result["activity_score"] > 0
    # Base calculation without quality adjustment would be:
    # (2 * 1.2) + (1 * 1.0) + (3 * 0.7) = 2.4 + 1.0 + 2.1 = 5.5
    # With quality adjustment (low quality), it should be less
    assert result["activity_score"] < 5.5


def test_participation_high_quality_reviews_boost():
    """
    Test that high-quality reviews boost participation score, addressing the edge case
    where someone provides excellent reviews but doesn't open many PRs.
    """
    # User with few PRs opened but high-quality review comments
    high_quality_comments = [
        "This function should be refactored because the loop can be simplified and would improve readability.",
        "Consider adding error handling here for edge cases that might cause runtime exceptions.",
        "The variable naming could be more descriptive to match the project's coding standards.",
    ]
    user = make_user(
        prs=1,  # Only 1 PR opened
        reviews=5,  # But reviewed 5 PRs with high quality
        issues=0,
        comments=0,
        review_comments=high_quality_comments,
    )
    
    result = compute_participation(user)
    
    # High-quality reviews should get a multiplier > 1.0 (up to 1.5)
    # So 5 reviews with high quality should contribute more than 5 * 1.0
    # The activity score should be: (1 * 1.2) + (5 * quality_multiplier)
    # With high quality (score ~4-5), multiplier should be ~1.3-1.5
    # So reviews contribute: 5 * 1.3 to 5 * 1.5 = 6.5 to 7.5
    # Total: 1.2 + 6.5 to 7.5 = 7.7 to 8.7
    assert result["activity_score"] > 7.0
    assert result["activity_score"] < 10.0
    
    # Compare to low-quality reviews
    low_quality_user = make_user(
        prs=1,
        reviews=5,
        issues=0,
        comments=0,
        review_comments=["ok", "nice"],  # Low quality
    )
    low_quality_result = compute_participation(low_quality_user)
    
    # Low-quality reviews should have lower participation score
    assert result["activity_score"] > low_quality_result["activity_score"]
