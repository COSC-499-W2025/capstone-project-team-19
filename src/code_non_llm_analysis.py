from src.code_complexity_analyzer import analyze_code_complexity, display_complexity_results
from src.git_individual_analyzer import analyze_git_individual_project, display_git_results

def run_code_non_llm_analysis(conn, user_id, project_name, zip_path):

    # Run complexity analysis
    complexity_data = analyze_code_complexity(conn, user_id, project_name, zip_path)
    if complexity_data:
        display_complexity_results(complexity_data)

    # Run git analysis
    git_data = analyze_git_individual_project(conn, user_id, project_name, zip_path)
    if git_data and git_data.get('has_git'):
        display_git_results(git_data)