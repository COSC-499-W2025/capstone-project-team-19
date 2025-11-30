from .code_complexity_analyzer import analyze_code_complexity, display_complexity_results
from .git_individual_analyzer import analyze_git_individual_project, display_git_results

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

    return {
        'complexity_data': complexity_data,
        'git_data': git_data
    }
    
def prompt_manual_code_project_summary(project_name: str) -> str:
    print(f"\n[NON-LLM] Let's capture a short summary for '{project_name}'.")
    print("Describe what the project does (purpose, main features, tech stack).")
    print("Use 1–3 sentences. Press ENTER on a blank line to finish.\n")

    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if not line.strip():
            break
        lines.append(line.strip())

    summary = " ".join(lines).strip()
    return summary or "[No manual project summary provided]"
