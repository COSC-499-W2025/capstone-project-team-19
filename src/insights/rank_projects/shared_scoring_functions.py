from src.models.project_summary import ProjectSummary

def skill_strength(project_summary: ProjectSummary) -> tuple[float, bool]:
    """
    Compute 0-1 skill strength score using detailed skills metrics
    Formula:
        weighted_score = score * level_multiplier (for each skill)
        avg_score = average of all weighted skill scores
        count_factor = min(num_skills / 10, 1)
        final = avg_score * count_factor
    
    Level multipliers:
        - Beginner: 0.3x (so max weighted score = 0.3)
        - Intermediate: 0.6x (so max weighted score = 0.6)
        - Advanced: 1.0x (so max weighted score = 1.0)
    
    This ensures that Advanced skills at lower scores rank higher than Beginner skills at high scores.
    Example: Advanced 0.5 (0.5 * 1.0 = 0.5) > Beginner 1.0 (1.0 * 0.3 = 0.3)
    """
    
    detailed = project_summary.metrics.get("skills_detailed", [])
    if not detailed:
        return 0.0, False
    
    # Level multipliers: higher levels get higher weights
    LEVEL_WEIGHTS = {
        "Beginner": 0.3,
        "Intermediate": 0.6,
        "Advanced": 1.0
    }
    
    weighted_scores = [] # create a list of all the weighted scores
    for skill in detailed:
        score = skill.get("score")
        level = skill.get("level", "Intermediate")  # default to Intermediate if level missing
        
        if isinstance(score, (float, int)):
            # Get level multiplier (default to Intermediate if level not recognized)
            level_multiplier = LEVEL_WEIGHTS.get(level, 0.6)
            # Weight the score by the level
            weighted_score = score * level_multiplier
            weighted_scores.append(weighted_score)
    
    if not weighted_scores:
        return 0.0, False

    avg_score = sum(weighted_scores) / len(weighted_scores) # get the average weighted score

    # if the project has 10+ skills, count_factor is 1 (the max possible value)
    # if the project has 5 skills, count_factor would be 0.5, etc.
    # if the project has 2 skills, the count_factor is 0.2, etc.
    count_factor = min(len(weighted_scores) / 10, 1)

    # combines the skill quality (weighted by level) with the skill quantity, so both are considered
    # Cap at 1.0 to ensure we stay within 0-1 range
    final_score = min(avg_score * count_factor, 1.0)
    return final_score, True

def contribution_strength(project_summary: ProjectSummary, is_collaborative: bool) -> tuple[float, bool]:
    """
    Compute 0-1 contribution strength
    - individual projects return 1.0
    - collaborative text = check text_collab['percent of document'] / 100
    - collaborative code = use metrics['github']['contribution_percent'] / 100
    - missing data = 0.0
    """

    # if it is an individual project, the user had full contribution
    if not is_collaborative:
        return 1.0, True

    text_collab = project_summary.contributions.get("text_collab")
    if isinstance(text_collab, dict) and "percent_of_document" in text_collab:
        percent = text_collab["percent_of_document"]
        if isinstance(percent, (int, float)):
            return max(0, min(percent / 100, 1)), True  # returns the highest value, cannot go lower than 0
        
    github_metrics = project_summary.metrics.get("github")
    if isinstance(github_metrics, dict) and "contribution_percent" in github_metrics:
        percent = github_metrics["contribution_percent"]
        if isinstance(percent, (int, float)):
            return max(0, min(percent / 100, 1)), True
        
    # no valid contribution percent
    return 0.0, False


def activity_diversity(project_summary: ProjectSummary, is_collaborative: bool) -> tuple[float, bool]:
    """
    Compute 0-1 activity diversity score
    uses either:
        - project_summary.metrics["activity_type"] (individual)
        - project_summary.contributions["activity_type"] (collaborative) 
    """

    activity = None

    # first attempt to get activity
    if is_collaborative: # primary location for collaborative
        activity = project_summary.contributions.get("activity_type")
    
    if activity is None:
        activity = project_summary.metrics.get("activity_type")

    if not isinstance(activity, dict):
        return 0.0, False

    number_of_activities = len(activity.keys())

    return min(number_of_activities / 5, 1.0), True  # 5+ types of activity is max diversity
