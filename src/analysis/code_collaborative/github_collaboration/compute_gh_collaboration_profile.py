from .normalized import compute_normalized_contribution
from .review_quality import compute_review_quality
from .participation import compute_participation
from .consistency import compute_consistency
from .leadership import compute_leadership
from src.analysis.skills.utils.skill_levels import classify_level

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

    
def compute_skill_levels(profile: dict) -> dict:
    skills = profile["skills"]

    review_q = skills["review_quality"]["score"]
    participation = skills["participation"]["activity_score"]

    c = skills["consistency"]
    consistency_score = c["active_weeks"] - c["burstiness"]

    leadership = skills["leadership"]["leadership_score"]

    return {
        "review_quality": classify_level(review_q, 5),
        "participation": classify_level(participation, 20),
        "consistency": classify_level(consistency_score, 12),
        "leadership": classify_level(leadership, 20),
    }