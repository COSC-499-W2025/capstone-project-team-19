from __future__ import annotations

# Each role maps to a list of (bucket_name, min_score) requirements.
# ALL requirements must be met for the role to be eligible.
# min_score is on a 0.0-1.0 scale matching your bucket scoring.

CODE_ROLES: dict[str, list[tuple[str, float]]] = {
    "Backend Developer":     [("api_and_backend", 0.3)],
    "Frontend Developer":    [("frontend_skills", 0.3)],
    "Full-Stack Developer":  [("api_and_backend", 0.3), ("frontend_skills", 0.3)],
    "Software Architect":    [("architecture_and_design", 0.5)],
    "QA / Test Engineer":    [("testing_and_ci", 0.4)],
    "Security Engineer":     [("security_and_error_handling", 0.4)],
    "Algorithms Engineer":   [("algorithms", 0.5), ("data_structures", 0.3)],
    "DevOps Engineer":       [("testing_and_ci", 0.3), ("security_and_error_handling", 0.3)],
    "Data Engineer":         [("data_structures", 0.4), ("algorithms", 0.3)],
    "Software Developer":    [("clean_code_and_quality", 0.3)],
}

TEXT_ROLES: dict[str, list[tuple[str, float]]] = {
    "Lead Author":          [("clarity", 0.5), ("structure", 0.4)],
    "Technical Writer":     [("clarity", 0.4), ("structure", 0.4), ("depth", 0.3)],
    "Research Analyst":     [("research", 0.4), ("argumentation", 0.3)],
    "Researcher":           [("research", 0.5)],
    "Academic Writer":      [("argumentation", 0.4), ("depth", 0.4), ("vocabulary", 0.3)],
    "Data Analyst":         [("data_analysis", 0.4), ("data_collection", 0.3)],
    "Content Strategist":   [("planning", 0.4), ("structure", 0.3)],
    "Editor":               [("process", 0.4), ("clarity", 0.3)],
}


def get_eligible_roles(
    project_type: str,
    bucket_scores: dict[str, float] | None,
) -> list[str]:
    """
    Returns eligible role names for a project type.
    If bucket_scores is None or empty, returns all roles for the type (no analysis yet).
    Otherwise filters by threshold requirements.
    """
    role_map = TEXT_ROLES if project_type == "text" else CODE_ROLES

    if not bucket_scores:
        return sorted(role_map.keys())

    eligible = []
    for role, requirements in role_map.items():
        if all(bucket_scores.get(bucket, 0.0) >= threshold for bucket, threshold in requirements):
            eligible.append(role)

    # Always return at least all roles as fallback if nothing qualifies
    return sorted(eligible) if eligible else sorted(role_map.keys())