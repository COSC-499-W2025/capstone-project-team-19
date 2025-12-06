from .code_complexity_analyzer import analyze_code_complexity, display_complexity_results
from .git_individual_analyzer import analyze_git_individual_project, display_git_results
from src.db.git_individual_metrics import (
    git_individual_metrics_exists,
    insert_git_individual_metrics,
    update_git_individual_metrics
)
from src.db.git_metrics_helpers import extract_git_metrics
import src.constants as constants

def run_code_non_llm_analysis(conn, user_id, project_name, zip_path, summary=None):

    # Run complexity analysis
    complexity_data = analyze_code_complexity(conn, user_id, project_name, zip_path)
    if summary and complexity_data:
        summary.metrics["complexity"] = complexity_data
    if complexity_data:
        display_complexity_results(complexity_data)

    # Run git analysis
    git_data = analyze_git_individual_project(conn, user_id, project_name, zip_path)
    if summary and git_data:
        summary.metrics["git"] = git_data
    if git_data and git_data.get('has_git'):
        display_git_results(git_data)
        # Store git metrics in database
        if conn:
            metrics = extract_git_metrics(git_data)
            update = git_individual_metrics_exists(conn, user_id, project_name)
            if update:
                update_git_individual_metrics(conn, user_id, project_name, *metrics)
            else:
                insert_git_individual_metrics(conn, user_id, project_name, *metrics)

            # Calculate totals for logging
            total_lines_added = metrics[7]  # index for total_lines_added
            total_commits = metrics[0]  # index for total_commits
            if constants.VERBOSE:
                print(f"[Git] Stored individual metrics for {project_name}: commits={total_commits}, lines added={total_lines_added}")

    return {
        'complexity_data': complexity_data,
        'git_data': git_data
    }
    
def prompt_manual_code_project_summary(project_name: str) -> str:
    print(f"\n[NON-LLM] PROJECT SUMMARY for '{project_name}'")
    print("Describe what the project does (purpose, main features, tech stack).")
    print("Write 1–3 sentences.\n")

    try:
        summary = input("Project summary: ").strip()
    except EOFError:
        summary = ""

    return summary or "[No manual project summary provided]"

