from src.insights.rank_projects import writing_quality, skill_strength, contribution_strength, activity_diversity, code_complexity, git_activity, github_collaboration, tech_stack

def _extract_base_scores(summary, is_collab):
    skill_strength_score, skill_available = skill_strength(summary)
    activity_div_score, activity_available = activity_diversity(summary, is_collab)

    results = [
        (skill_strength_score, skill_available, 0.30),
        (activity_div_score, activity_available, 0.10),
    ]
    
    # Only include contribution_strength for collaborative projects
    # For individual projects, contribution is always 1.0, so it doesn't provide meaningful differentiation
    if is_collab:
        cont_strength_score, cont_available = contribution_strength(summary, is_collab)
        results.append((cont_strength_score, cont_available, 0.20))
    
    return results

def _extract_text_scores(summary):
    writing_quality_score, writing_available = writing_quality(summary)
    return [(writing_quality_score, writing_available, 0.40)]

def _extract_code_scores(summary, is_collab):
    code_complex_score, code_complexity_available = code_complexity(summary)
    git_activity_score, git_activity_available = git_activity(summary)
    github_collab_score, github_collab_available = github_collaboration(summary)
    tech_stack_score, tech_stack_available = tech_stack(summary)

    return [
        (code_complex_score, code_complexity_available, 0.25),
        (git_activity_score, git_activity_available, 0.20),
        (github_collab_score, github_collab_available, 0.03),
        (tech_stack_score, tech_stack_available, 0.15)
    ]