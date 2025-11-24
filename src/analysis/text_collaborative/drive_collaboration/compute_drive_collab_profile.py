from .comment_quality import compute_comment_quality
from .participation import compute_participation
from .communication_leadership import compute_communication_leadership

from .models import RawUserTextCollabMetrics, RawTeamTextCollabMetrics


def compute_text_collaboration_profile(
    user: RawUserTextCollabMetrics,
    team: RawTeamTextCollabMetrics
) -> dict:
    """
    Convert raw Drive metrics into a structured collaboration-skill profile.
    """
    # TODO: Add normalized contribution if needed
    normalized = {}  # Placeholder for now

    comment_quality = compute_comment_quality(user.comment_texts)
    participation = compute_participation(user)
    communication_leadership = compute_communication_leadership(user)

    return {
        "normalized": normalized,
        "skills": {
            "comment_quality": comment_quality,
            "participation": participation,
            "communication_leadership": communication_leadership,
        }
    }


def classify_level(value: float, max_value: float) -> str:
    if max_value <= 0:
        return "Beginner"
    
    ratio = value / max_value

    if ratio < 0.33:
        return "Beginner"
    elif ratio < 0.66:
        return "Intermediate"
    else:
        return "Advanced"
    

def compute_skill_levels(profile: dict) -> dict:
    skills = profile["skills"]

    comment_q = skills["comment_quality"]["score"]
    participation = skills["participation"]["activity_score"]
    leadership = skills["communication_leadership"]["leadership_score"]

    return {
        "comment_quality": classify_level(comment_q, 5),
        "participation": classify_level(participation, 20),
        "communication_leadership": classify_level(leadership, 20),
    }