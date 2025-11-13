from src.github.db_repo_metrics import get_github_repo_metrics
from src.github.link_repo import get_gh_repo_name_and_owner
from src.llm_utils import generate_summary

def interpret_code_contributions(conn, user_id, project_name, external_consent):
    metrics = fetch_all_code_metrics(conn, user_id, project_name)

    if external_consent == "accepted":
        interpretation = interpret_code_with_llm(conn, user_id, project_name, metrics)
    else:
        interpretation = interpret_code_without_llm(conn, user_id, project_name, metrics)

    summary_points = interpretation.get("summary_points", [])
    return {
        "project_name": project_name,
        "metrics": metrics,
        "summary_points": summary_points,
        "formatted_summary": format_summary_points(summary_points)
    }
    
def interpret_code_with_llm(conn, user_id, project_name, metrics):
    # Uses an LLM to produce resume-style statements and key highlights from code contribution metrics.

    prompt = f"""
    You are analyzing contribution data for a collaborative coding project named '{project_name}'.
    Given these metrics:
    {metrics}

    Write 3-5 concise resume-style bullet points highlighting impact, collaboration, and technical scope.
    Each bullet should sound professional and accomplishment-oriented.
    Output each bullet on a new line starting with '- '.
    """

    try:
        summary_text = generate_summary(prompt).strip()

        # Normalize to real bullet lines (handles either '-' or sentences)
        lines = summary_text.split("\n")
        summary_points = []
        for line in lines:
            cleaned = line.strip("-• ").strip()
            if cleaned:
                summary_points.append(cleaned)

        # If LLM returned a paragraph, split into sentences
        if len(summary_points) == 1 and ". " in summary_points[0]:
            sentences = [s.strip() for s in summary_points[0].split(". ") if s.strip()]
            summary_points = [s + "." for s in sentences][:5]

        if not summary_points:
            summary_points = ["Automated summary unavailable."]
    except Exception as e:
        print(f"[LLM ERROR] Failed to generate summary: {e}")
        summary_points = ["Automated summary unavailable."]

    return {
        "summary_points": summary_points,
        "highlights": metrics.get("github", {}),
        "score": None
    }


def interpret_code_without_llm(conn, user_id, project_name, metrics):
    # Generate resume insighs from Github and local git metrics WITHOUT LLM

    gh = metrics.get("github", {}) or {}
    local = metrics.get("local_git", {}) or {}

    summary_points = []

    # GitHub contributions
    commits = gh.get("total_commits")
    prs = gh.get("prs_merged") or 0
    issues = gh.get("issues_closed") or 0
    additions = gh.get("total_additions") or 0
    deletions = gh.get("total_deletions") or 0
    contribution = gh.get("contribution_percent")

    if commits:
        summary_points.append(f"Contributed {commits} commits to the repository.")
    if prs or issues:
        summary_points.append(f"Reviewed and merged {prs} pull requests, resolving {issues} issues.")
    if additions or deletions:
        summary_points.append(f"Modified {additions + deletions:,} lines of code across multiple files.")
    if contribution:
        summary_points.append(f"Accounted for approximately {contribution:.1f}% of total project activity.")

    # Local .git metrics (if available)
    if local:
        if local.get("active_days"):
            summary_points.append(f"Maintained consistent contributions over {local['active_days']} active days.")
        if local.get("languages"):
            langs = ", ".join(local["languages"])
            summary_points.append(f"Worked primarily in {langs} throughout the project.")

    # Fallback if nothing found
    if not summary_points:
        summary_points.append("Contributed to codebase development and collaborative version control.")

    return {
        "summary_points": summary_points,
        "highlights": {
            "commits": commits,
            "prs_merged": prs,
            "issues_closed": issues,
            "total_additions": additions,
            "total_deletions": deletions,
            "contribution_percent": contribution
        },
        "score": None
    }

def fetch_all_code_metrics(conn, user_id, project_name):
    """Retrieve GitHub + local git metrics for a project."""
    git_file_metrics = {}  # placeholder until local metrics are added

    owner, repo = get_gh_repo_name_and_owner(conn, user_id, project_name)
    github_api_metrics = {}

    if owner and repo:
        github_api_metrics = get_github_repo_metrics(conn, user_id, project_name, owner, repo) or {}
    else:
        print(f"[INFO] No linked GitHub repo found for {project_name}. Skipping GitHub metrics.")

    if not github_api_metrics:
        print(f"[WARN] No GitHub metrics found for {project_name}.")
    if not git_file_metrics:
        print(f"[WARN] No local git metrics found for {project_name}.")

    return {
        "github": github_api_metrics,
        "local_git": git_file_metrics
    }

def format_summary_points(summary_points):
    """Format summary points as bullet list string."""
    return "\n".join(f" - {p}" for p in summary_points if p)
