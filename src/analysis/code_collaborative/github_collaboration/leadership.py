from .models import RawUserCollabMetrics

def compute_leadership(user: RawUserCollabMetrics):
    """
    Leadership = initiative + ability to review others' work.
    """

    # Weighting rationale: Issues opened (1.4) weighted higher than PRs opened (1.2) because
    # identifying problems and proposing solutions demonstrates stronger initiative.
    # PRs reviewed (1.0) serves as the baseline weight for comparison.
    initiator = user.prs_opened * 1.2 + user.issues_opened * 1.4
    reviewer = user.prs_reviewed * 1.0

    balance = abs(initiator - reviewer)

    return {
        "initiator_score": initiator,
        "reviewer_score": reviewer,
        "balance_score": balance,
        "leadership_score": initiator + reviewer,
    }
