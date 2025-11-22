from .models import RawUserCollabMetrics

def compute_participation(user: RawUserCollabMetrics):
    """
    Compute how broadly and actively the user participates across project surfaces.
    """

    channels_used = sum([
        user.prs_opened > 0,
        user.prs_reviewed > 0,
        user.issues_opened > 0,
        user.issue_comments > 0,
        len(user.review_comments) > 0,
    ])

    # Weighted activity score: Higher weights for actions that drive project progress.
    # Issues opened (1.3) and PRs opened (1.2) are weighted higher as they represent
    # proactive contributions. PRs reviewed (1.0) is the baseline. Issue comments (0.7)
    # are weighted lower as they are reactive responses rather than initiating actions.
    activity_score = (
        user.prs_opened * 1.2 +
        user.prs_reviewed * 1.0 +
        user.issues_opened * 1.3 +
        user.issue_comments * 0.7
    )

    return {
        "channels_used": channels_used,
        "activity_score": activity_score,
    }
