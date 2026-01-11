import json

from src.db import get_all_user_project_summaries, get_project_rank
from src.models.project_summary import ProjectSummary
from src.insights.rank_projects.extract_scores import _extract_base_scores, _extract_code_scores, _extract_text_scores

def collect_project_data(conn, user_id, respect_manual_ranking=True):
    project_scores = []
    rows = get_all_user_project_summaries(conn, user_id)

    for row in rows:
        project_name = row["project_name"]
        project_type = row["project_type"]
        summary_dict = json.loads(row["summary_json"])
        project_summary = ProjectSummary.from_dict(summary_dict)

        is_collaborative = (project_summary.project_mode == "collaborative")

        results = _extract_base_scores(project_summary, is_collaborative)

        if project_type == "text":
            results += _extract_text_scores(project_summary)

        else: # project will be code
            results += _extract_code_scores(project_summary, is_collaborative)

        auto_score = combine_scores(results)

        # Get manual rank if exists
        manual_rank = None
        if respect_manual_ranking:
            manual_rank = get_project_rank(conn, user_id, project_name)

        project_scores.append((project_name, auto_score, manual_rank))

    # Sort: manual rankings first (ascending), then auto-score (descending)
    project_scores.sort(key=lambda x: (
        0 if x[2] is not None else 1,  # Manual ranks come first
        x[2] if x[2] is not None else 0,  # Lower rank number = higher priority
        -x[1]  # Higher score = higher priority
    ))

    # Return just (name, score) for backward compatibility
    return [(name, score) for name, score, _ in project_scores]

def combine_scores(results: list):
    """
    Calculate weighted final score by combining normalized component scores.
    
    The final score is computed as: weighted_sum / total_weight, where each component
    score is multiplied by its assigned weight before summing. This ensures that
    different metrics contribute proportionally to the final importance ranking.
    
    Weight Distribution Rationale:
    
    Base Scores (applied to all projects):
    - Skill Strength (30%): The most important factor as it directly measures technical
      competency demonstrated in the project. Higher weight reflects that skills are
      the primary indicator of project importance for career development.
    
    - Activity Diversity (10%): Lower weight because while diverse activities show
      versatility, it's less critical than skill depth for ranking importance.
    
    - Contribution Strength (20%, collaborative only): Measures individual impact in
      team projects. Only included for collaborative projects since individual projects
      always have 100% contribution. Weighted to reflect collaborative work's importance
      but not as heavily as skill strength.
    
    Text Project Additions:
    - Writing Quality (40%): Primary differentiator for text projects, weighted heavily
      to emphasize communication and writing skills which are core to text-based work.
    
    Code Project Additions:
    - Code Complexity (25%): High weight reflects that complex code demonstrates
      advanced problem-solving and technical depth.
    
    - Git Activity (20%): Represents development engagement and workflow maturity,
      important but secondary to code quality.
    
    - Tech Stack (15%): Measures breadth of technologies used, weighted moderately
      as variety is valuable but not as important as code quality.
    
    - GitHub Collaboration (3%): Minimal weight as this metric is often unavailable
      or less reliable, and collaboration is already captured in contribution_strength
      for collaborative projects.
    
    Note: Weights are normalized dynamically - if a score is unavailable, its weight
    is excluded from total_weight, so the final score represents the weighted average
    of only available metrics. This ensures projects aren't penalized for missing
    optional data points.
    """
    weighted_sum = 0.0
    total_weight = 0.0

    # do not consider scores that our system could not access (meaning if the project summary did not contain any info on the score we do not count it)
    # this ensures that if we DO get insights into a certain metrics, but the user is "bad" at it and gets a score of 0, it is counted
    for score, available, weight in results:
        if available:
            weighted_sum += score * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0
    
    # Calculate weighted average: sum of (score * weight) divided by sum of weights
    # Example: scores=[0.8, 0.6], weights=[0.3, 0.7] → (0.8*0.3 + 0.6*0.7) / (0.3+0.7) = 0.66
    return weighted_sum / total_weight
