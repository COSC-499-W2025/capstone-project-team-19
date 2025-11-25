from src.db import get_project_summaries, get_file_metrics, get_github_repo_metrics, get_commit_timestamps, get_text_non_llm_metrics, get_text_contribution_summary, get_project_skills, get_code_activity_metrics

# get all project summaries and projecs for the user
def collect_project_data(conn, user_id):
    # Collect all necessary data per project to prepare scoring
    summaries = get_project_summaries
    projects = []

    for summary in summaries:
        name = summary["project_name"]
        data = {
            "project_name": name,
            "summary": summary,
            "file_metrics": get_file_metrics(conn, user_id, name),
            "repo_metrics": get_github_repo_metrics(conn, user_id, name),
            "commit_timestamps": get_commit_timestamps(conn, user_id, name),
            "text_metrics": get_text_non_llm_metrics(conn, user_id, name),
            "text_contrib": get_text_contribution_summary(conn, user_id, name),
            "skills": get_project_skills(conn, user_id, name),
            "activity": get_code_activity_metrics(conn, user_id, name),
        }

        projects.append(data)

    return projects

def score_project(project):
    def score_project(p):
    """Compute final importance score for one project."""
    s = p["summary"]
    files = p["file_metrics"]
    repo = p["repo_metrics"]
    skills = p["skills"]
    commits = p["commit_timestamps"]
    text = p["text_metrics"]
    text_contrib = p["text_contrib"]
    activity = p["activity"]

    # TODO: either implement the functions or see if other functions can be reused
    complexity_score = compute_complexity(s, repo, text)
    contribution_score = compute_contribution(s, repo, text_contrib, activity)
    size_score = compute_size(files, text)
    skill_score = compute_skill_score(skills, s)
    recency_score = compute_recency(s, files, repo, commits)
    breadth_score = compute_breadth(s)
    duration_score = compute_duration(repo, commits)
    error_penalty = len(s.get("errors", []))

    importance_score = (
        0.25 * complexity_score +
        0.20 * contribution_score +
        0.15 * size_score +
        0.15 * skill_score +
        0.10 * recency_score +
        0.10 * breadth_score +
        0.04 * duration_score -
        0.10 * error_penalty
    )

    return max(importance_score, 0)

# TODO: print the projects