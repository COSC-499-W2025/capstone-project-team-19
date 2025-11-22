from .models import RawUserCollabMetrics
from .review_quality import compute_review_quality

def compute_participation(user: RawUserCollabMetrics):
    """
    Compute how broadly and actively the user participates across project surfaces.
    
    Addresses edge case: High-quality reviews are weighted more heavily to ensure
    that reviewers who provide substantive feedback are recognized even if they
    don't open many PRs themselves.
    """

    channels_used = sum([
        user.prs_opened > 0,
        user.prs_reviewed > 0,
        user.issues_opened > 0,
        user.issue_comments > 0,
        len(user.review_comments) > 0,
    ])

    # Compute review quality to adjust PR review weight
    # Review quality score is 0-5, so we normalize to a multiplier (0.5 to 1.5)
    # This means high-quality reviews (score 4-5) can boost participation significantly
    review_quality = compute_review_quality(user.review_comments)
    quality_multiplier = 0.5 + (review_quality["score"] / 5) * 1.0  # Range: 0.5 to 1.5
    
    # Base weight for PR reviews is 1.0, but gets adjusted by quality
    # High-quality reviews (score 5) get 1.5x weight, low-quality (score 0) get 0.5x
    pr_review_weight = 1.0 * quality_multiplier

    # Weighted activity score: Higher weights for actions that drive project progress.
    # Issues opened (1.3) and PRs opened (1.2) are weighted higher as they represent
    # proactive contributions. PRs reviewed weight is adjusted by review quality to
    # address the edge case where someone opens low-effort PRs but others provide
    # high-quality reviews. Issue comments (0.7) are weighted lower as they are
    # reactive responses rather than initiating actions.
    activity_score = (
        user.prs_opened * 1.2 +
        user.prs_reviewed * pr_review_weight +
        user.issues_opened * 1.3 +
        user.issue_comments * 0.7
    )

    return {
        "channels_used": channels_used,
        "activity_score": activity_score,
    }
