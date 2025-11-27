import json

from src.db import get_project_summaries, get_file_metrics, get_github_repo_metrics, get_commit_timestamps, get_text_non_llm_metrics, get_text_contribution_summary, get_project_skills, get_code_activity_metrics
from src.db.connection import connect
from src.insights.project_ranking.scoring_functions import compute_complexity, compute_contribution, compute_size, compute_skill_score, compute_recency, compute_breadth, compute_duration

# get all project summaries and projecs for the user
def collect_project_data(conn, user_id):
    summaries = get_project_summaries(conn, user_id)
    projects = []

    for summary in summaries:

        # extract basic fields directly from DB row
        project_name = summary["project_name"]
        project_type = summary["project_type"] # code or text
        project_mode = summary["project_mode"] # individual or collaborative

        # parse stored JSON
        summary_json = json.loads(summary["summary_json"])

        """
        print("\n======== RAW SUMMARY JSON FOR", project_name, "========")
        print(json.dumps(summary_json, indent=2))
        print("===============================================\n")
        """

        # GitHub extraction (and checking if this should even be called with variable should_get_github)
        github = summary_json.get("github", {}) or {}
        exists = github.get("exists", False)
        owner = github.get("owner")
        repo = github.get("repo")

        should_get_github = (project_type == "code" and project_mode == "collaborative" and exists and owner and repo)

        # now conditional DB calls
        if should_get_github:
            repo_metrics = get_github_repo_metrics(conn, user_id, project_name, owner, repo)
            activity = get_code_activity_metrics(conn, user_id, project_name)
        else:
            repo_metrics = None
            activity = None

        # always safe queries
        file_metrics = get_file_metrics(conn, user_id, project_name)
        commit_timestamps = get_commit_timestamps(conn, user_id, project_name)
        text_metrics = get_text_non_llm_metrics(conn, user_id, project_name)
        text_contrib = get_text_contribution_summary(conn, user_id, project_name)
        skills = get_project_skills(conn, user_id, project_name)

        projects.append({
            "project_name": project_name,
            "summary": summary_json,
            "file_metrics": file_metrics,
            "repo_metrics": repo_metrics,
            "commit_timestamps": commit_timestamps,
            "text_metrics": text_metrics,
            "text_contrib": text_contrib,
            "skills": skills,
            "activity": activity
        })

    return projects

def score_project(project, conn=None, user_id=None):
    # print everything first, to see what you are working with
    if conn is not None and user_id is not None:
        print("Conn and user_id exist.")
        print("Calling collect_project_data BRO")
        projects = collect_project_data(conn, user_id)

    """Compute final importance score for one project."""
    s = project["summary"]
    files = project["file_metrics"]
    repo = project["repo_metrics"]
    skills = project["skills"]
    commits = project["commit_timestamps"]
    text = project["text_metrics"]
    text_contrib = project["text_contrib"]
    activity = project["activity"]

    # TODO: either implement the functions or see if other functions can be reused
    complexity_score = compute_complexity(s, repo, text)
    contribution_score = compute_contribution(s, repo, text_contrib, activity)
    size_score = compute_size(files, text)
    skill_score = compute_skill_score(skills, s)
    recency_score = compute_recency(s, files, repo, commits)
    breadth_score = compute_breadth(s)
    duration_score = compute_duration(repo, commits)
    error_penalty = len(s.get("errors", []))

"""
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
"""

if __name__ == "__main__":
    conn = connect()
    #user_id = int(sys.argv[1]) if len(sys.argv) > 1 else conn.execute("SELECT user_id FROM users LIMIT 1").fetchone()[0]
    user_id = 2
    print("Calling collect_project_data BRUH")
    projects = collect_project_data(conn, user_id) # TODO: change to get the number of projects the user has in the db

    for project in projects:
        score_project(project, conn, user_id)

    conn.close()