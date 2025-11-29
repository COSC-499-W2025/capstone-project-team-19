from src.models.project_summary import ProjectSummary

def code_complexity_score(ps: ProjectSummary) -> float:
    """
    Compute 0-1 code complexity score using:
        - total files
        - total lines
        - total functions
        - cyclomatic complexity
        - maintainability index
    Uses normalized values (with caps) to avoid huge projects autokmatiucally dominating the score
    """

    complexity = ps.metrics.get("complexity")
    if not isinstance(complexity, dict):
        return 0.0
    
    summary = complexity.get("summary")
    if not isinstance(summary, dict):
        return 0.0
    
    # Extract fields safely
    total_files = summary.get("total_files", 0)
    total_lines = summary.get("total_lines", 0)
    total_functions = summary.get("total_functions", 0)
    avg_cyclo = summary.get("avg_complexity", 0)
    maintainability = summary.get("maintainability_index", None)

    # cap everything so massive repos dont inflate the score
    file_score = min(total_files / 40, 1.0) # 40+ files = max
    line_score = min(total_lines / 10000, 1.0) # 10,000 + lines = max
    function_score = min(total_functions / 100, 1.0) # 100+ functions = max

    # cyclomatic complexity means the higher it is the more complex
    # if it is higher than 10 it may be too complex, so normalize to 10
    cyclo_score = min(avg_cyclo / 10, 1.0)

    if isinstance(maintainability, (float, int)):
        maintainability_score = min(max(maintainability / 100, 0), 1.0)
    else:
        maintainability_score = 0.5 # neutral if the maintainability score does not exist

    # weighted final score
    final_score = (0.25 * file_score) + (0.25 * line_score) + (0.20 * function_score) + (0.15 * cyclo_score) + (0.15 * maintainability_score)

    return max(0.0, min(final_score, 1.0))

def git_activity_score(ps: ProjectSummary) -> float:
    """
    Score the git activity of a code project from 0-1
    Based on:
        - total commits
        - days active
        - length of commit history
        - consistency of commits
    """

    git = ps.metrics.get("git")
    if not isinstance(git, dict):
        return 0.0

    stats = git.get("commit_stats", {})
    if not isinstance(stats, dict):
        return 0.0

    total_commits = stats.get("total_commits", 0)
    active_days = stats.get("active_days", 0)
    commit_span = stats.get("commit_span_days", 0) # days between first and last commit

    # Normalize components
    commit_score = min(total_commits / 80, 1.0) # 80+ commits = max
    activity_score = min(active_days / 30, 1.0) # active 30 days = max
    span_score = min(commit_span / 60, 1.0) # 2 month commit window = max

    # Weighted sum
    final_score = (0.45 * commit_score) + (0.30 * activity_score) + (0.25 * span_score)

    return max(0.0, min(final_score, 1.0))


def github_collaboration_score(ps: ProjectSummary) -> float:
    """
    Score GitHub collaboration metrics from 0-1
    Only applies to collaborative code projects with GitHub data
    """

    gh = ps.metrics.get("github")
    if not isinstance(gh, dict):
        return 0.0

    prs = gh.get("prs_opened", 0)
    issues = gh.get("issues_opened", 0)
    contrib_percent = gh.get("contribution_percent", 0)
    additions = gh.get("total_additions", 0)
    deletions = gh.get("total_deletions", 0)

    # Normalize each score
    pr_score = min(prs / 20, 1.0) # 20 PRs = max
    issue_score = min(issues / 20, 1.0) # 20 issues = max
    contribution_score = min(contrib_percent / 100, 1.0)
    churn_score = min((additions + deletions) / 15000, 1.0) # 15,000 lines of code changed = high impact

    final_score = (0.30 * contribution_score) + (0.25 * pr_score) + (0.25 * issue_score) + (0.20 * churn_score)

    return max(0.0, min(final_score, 1.0))


def tech_stack_score(ps: ProjectSummary) -> float:
    """
    Score the technical stack depth from 0-1
    Based on number of languages and frameworks used
    """

    languages = ps.languages or []
    frameworks = ps.frameworks or []

    language_score = min(len(languages) / 4, 1.0) # 4+ languages = max
    frameworks_score = min(len(frameworks) / 3, 1.0) # 3+ frameworks = max

    final_score = (0.6 * language_score) + (0.4 * frameworks_score)

    return max(0.0, min(final_score, 1.0))


def code_contribution_strength(ps: ProjectSummary, is_collaborative: bool) -> float:
    """
    Score collaboration contribution for code projects from 0-1
    Uses:
        - GitHub contribution_percent if available
        - Otherwise falls back to 0.0 for collaborative
        - Individual projects always return 1.0
    """

    if not is_collaborative:
        return 1.0

    gh = ps.metrics.get("github")
    if isinstance(gh, dict):
        percent = gh.get("contribution_percent")
        if isinstance(percent, (float, int)):
            return max(0.0, min(percent / 100, 1.0))

    return 0.0
