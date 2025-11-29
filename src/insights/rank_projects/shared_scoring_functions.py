from src.models.project_summary import ProjectSummary

def skill_strength(project_summary: ProjectSummary) -> float:
    """
    Compute 0-1 skill strength score using detailed skills metrics
    Formula:
        avg_score = average of all skill scores (0-1)
        count_factor = min(num_skills / 10, 1)
        final = avg_score * count_factor
    """
    
    detailed = project_summary.metrics.get("skills_detailed", [])
    if not detailed:
        return 0.0
    
    scores = [] # create a list of all the different scores
    for skill in detailed:
        score = skill.get("score")
        if isinstance(score, (float, int)):
            scores.append(score)
    
    if not scores: return 0.0

    avg_score = sum(scores) / len(scores) # get teh avergae score

    # if the project has 10+ skills, count_factor is 1 (the max possible value)
    # if the project has 5 skills, count_factor would be 0.5, etc.
    # if the project has 2 skills, the count_factor is 0.2, etc.
    count_factor = min(len(scores) / 10, 1)

    # combines the skill quality with the skill quantity, so both are considered
    return avg_score * count_factor

def contribution_strength(project_summary: ProjectSummary, is_collaborative: bool) -> float:
    """
    Compute 0-1 contribution strength
    - individual projects return 1.0
    - collaborative text = check text_collab['percent of document'] / 100
    - collaborative code = use metrics['github']['contribution_percent'] / 100
    - missing data = 0.0
    """

    # if it is an individual project, the user had full contribution
    if not is_collaborative: return 1.0

    text_collab = project_summary.contributions.get("text_collab")
    if isinstance(text_collab, dict) and "percent_of_document" in text_collab:
        percent = text_collab["percent_of_document"]
        if isinstance(percent, (int, float)):
            return max(0, min(percent / 100, 1)) # returns the highest value, cannot go lower than 0
        
    github_metrics = project_summary.metrics.get("github")
    if isinstance(github_metrics, dict) and "contribution_percent" in github_metrics:
        percent = github_metrics["contribution_percent"]
        if isinstance(percent, (int, float)):
            return max(0, min(percent / 100, 1))
        
    return 0.0 # no valid contribution percent


def activity_diversity(project_summary: ProjectSummary, is_collaborative: bool) -> float:
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


    if not isinstance(activity, dict): return 0.0

    number_of_activities = len(activity.keys())

    return min(number_of_activities / 5, 1.0) # 5+ types of activity is max diversity
