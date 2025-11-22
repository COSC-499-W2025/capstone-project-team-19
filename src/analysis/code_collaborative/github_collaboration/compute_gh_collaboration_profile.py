from .normalized import compute_normalized_contribution
from .review_quality import compute_review_quality
from .participation import compute_participation
from .consistency import compute_consistency
from .leadership import compute_leadership

from .models import RawUserCollabMetrics, RawTeamCollabMetrics


def compute_collaboration_profile(
    user: RawUserCollabMetrics,
    team: RawTeamCollabMetrics
) -> dict:
    """
    Convert raw GitHub metrics into a structured collaboration-skill profile.
    """

    normalized = compute_normalized_contribution(user, team)
    review_quality = compute_review_quality(user.review_comments)
    participation = compute_participation(user)
    consistency = compute_consistency(
        user.commit_timestamps,
        user.pr_timestamps,
        user.review_timestamps
    )
    leadership = compute_leadership(user)

    return {
        "normalized": normalized,
        "skills": {
            "review_quality": review_quality,
            "participation": participation,
            "consistency": consistency,
            "leadership": leadership,
        }
    }
