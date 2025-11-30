import math
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
    Compute a 0-1 activity diversity score using normalized Shannon entropy.
    
    What this function does:
        - Extracts activity counts from either collaborative contributions or individual metrics (supports both simple and complex formats)
        - Converts raw counts into proportions of total activity
        - Computes Shannon entropy: the negative sum of (p * log2(p)) for every activity proportion p 
          (so the value returned is higher when activities are evenly distirbuted, and lower when they are not)
        - Normalizes by the theoretical maximum entropy for N activity types to produce a 0-1 balance score
        - Applies an activity-count scaling factor so projects with more activity types can reach higher potential diversity (up to 5 types, so capped at 5)

    Result:
    Returns a mathematical diversity score where:
        - 0.0 means all activity types are concentrated in one activity
        - 1.0 means the activity types are evenly distributed amongst one another
        - Intermediate values reflect both the number of activities and how balanced the distribution is
    
    Why this works:
        - Shannon entropy rewards activity distributions that are more balanced and penalizes activity distributions where one activity dominates the project
        - Unlike simple activity counts or threshold checks, entropy prevents small activitys (e.g. 0.05% documentation) from inflating the diversity score
    """

    # Get activity data (collab first, fallback to metrics)
    activity = None

    if is_collaborative:
        activity = project_summary.contributions.get("activity_type")

    if activity is None:
        activity = project_summary.metrics.get("activity_type")

    if not isinstance(activity, dict):
        return 0.0, False
    
    """
    Extract numerical activity counts
    Supports both simple and complex counts (e.g. {"coding": 12} AND {"coding": {"count": 12, ...}})
    """
    activity_counts = {}
    for name, value in activity.items():
        if isinstance(value, dict):
            count = value.get("count", 0)
        else:
            count = value

        if isinstance(count, (int, float)) and count > 0:
            activity_counts[name] = count

    if not activity_counts:
        return 0.0, False
    
    # basic properties
    total = sum(activity_counts.values())
    num_types = len(activity_counts)

    if total == 0 or num_types == 1:
        return 0.0, True # data exists but there is no diversity
    
    """
    Compute normalized Shannon entropy:
        entropy = -sum(p * log2(p)
        max_entropy = log2(num_types)
        normalized = entropy / max_entropy

        `entropy`: The actual distribution the data (activity_types) creates
        `max_entropy`: For N activity types the maximum possible Shannon entropy occurs when all activity types are perfectly evenly distributed (documentation: 33%, feature coding: 33%, testing: 33%)
    """
    proportions = [count / total for count in activity_counts.values()]

    entropy = 0.0
    for p in proportions:
        entropy -= p * math.log2(p)

    max_entropy = math.log2(num_types)
    normalized_entropy = entropy / max_entropy

    # scale by activity count factor
    count_factor = min(num_types / 5.0, 1.0)

    diversity = normalized_entropy * count_factor
    return min(diversity, 1.0), True
