from .written_communication import compute_written_communication
from .participation import compute_participation
from .communication_leadership import compute_communication_leadership
from src.analysis.skills.utils.skill_levels import classify_level

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

    written_communication = compute_written_communication(user.comment_texts)
    participation = compute_participation(user)
    communication_leadership = compute_communication_leadership(user)

    return {
        "normalized": normalized,
        "skills": {
            "written_communication": written_communication,
            "participation": participation,
            "communication_leadership": communication_leadership,
        }
    }

def compute_skill_levels(profile: dict) -> dict:
    skills = profile["skills"]

    written_comm = skills["written_communication"]["score"]
    participation = skills["participation"]["activity_score"]
    leadership = skills["communication_leadership"]["leadership_score"]

    return {
        "written_communication": classify_level(written_comm, 5),
        "participation": classify_level(participation, 20),
        "communication_leadership": classify_level(leadership, 20),
    }