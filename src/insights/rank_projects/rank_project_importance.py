import json

from src.db import get_all_user_project_summaries
from src.models.project_summary import ProjectSummary
from src.insights.rank_projects.extract_scores import _extract_base_scores, _extract_code_scores, _extract_text_scores

def collect_project_data(conn, user_id):
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
        
        final_score = combine_scores(results)
        project_scores.append((project_name, final_score))

    # sort by score descending
    project_scores.sort(key=lambda x: x[1], reverse=True)
    return project_scores

def combine_scores(results: list):
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
    
    # takes the sum of the scores and divides by the total number of scores (ex.: project score = (0.8 + 0.6 + 0.4) / 3)
    # this assumes all scores are equal, meaning the score is not weighted
    return weighted_sum / total_weight
