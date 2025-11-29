"""
src/menu/resume.py

Menu option for viewing resume items.
"""

import json
from typing import List

from src.db import get_all_user_project_summaries
from src.models.project_summary import ProjectSummary


def view_resume_items(conn, user_id: int, username: str):
    """
    Load stored project summaries for the user and prepare them for resume display.
    """
    summaries = _load_project_summaries(conn, user_id)
    print(f"\n[Resume] Loaded {len(summaries)} project summary record(s) for {username}.")
    _render_resume(summaries)


def _load_project_summaries(conn, user_id: int) -> List[ProjectSummary]:
    """
    Fetch and deserialize all saved project summaries for the user.
    """
    rows = get_all_user_project_summaries(conn, user_id)
    projects: List[ProjectSummary] = []

    for row in rows:
        try:
            summary_dict = json.loads(row["summary_json"])
            projects.append(ProjectSummary.from_dict(summary_dict))
        except Exception:
            # Skip malformed entries to avoid breaking the resume flow.
            continue

    return projects


def _render_resume(summaries: List[ProjectSummary]) -> None:
    """
    Render per-project resume blocks and aggregate skills.
    """
    if not summaries:
        print("No project summaries available yet. Run an analysis first.")
        return

    # Group projects
    code_indiv = []
    code_collab = []
    text_indiv = []
    text_collab = []

    for ps in summaries:
        if ps.project_type == "code":
            (code_collab if ps.project_mode == "collaborative" else code_indiv).append(ps)
        elif ps.project_type == "text":
            (text_collab if ps.project_mode == "collaborative" else text_indiv).append(ps)

    # Render sections
    if code_indiv:
        print("\n=== Code Projects (Individual) ===")
        for ps in code_indiv:
            _render_code_project(ps)

    if code_collab:
        print("\n=== Code Projects (Collaborative) ===")
        for ps in code_collab:
            _render_code_project(ps, collaborative=True)

    if text_indiv:
        print("\n=== Text Projects (Individual) ===")
        for ps in text_indiv:
            _render_text_project(ps)

    if text_collab:
        print("\n=== Text Projects (Collaborative) ===")
        for ps in text_collab:
            _render_text_project(ps, collaborative=True)

    _render_aggregated_skills(summaries)


def _render_code_project(ps: ProjectSummary, collaborative: bool = False) -> None:
    print(f"\n- {ps.project_name}")
    if ps.languages:
        print(f"  Languages: {', '.join(sorted(set(ps.languages)))}")
    if ps.frameworks:
        print(f"  Frameworks: {', '.join(sorted(set(ps.frameworks)))}")

    if ps.summary_text:
        print(f"  Summary: {ps.summary_text}")

    # Activity types with top file (if available)
    activity = None
    if collaborative:
        activity = ps.contributions.get("activity_type")
    activity = activity or ps.metrics.get("activity_type")
    if isinstance(activity, dict):
        print("  Contributions:")
        for k, v in activity.items():
            top_file = v.get("top_file") or v.get("top_file_overall")
            top_info = f" (top: {top_file})" if top_file else ""
            print(f"    • {k}{top_info}")

    # Skills demonstrated
    skills = _extract_skills(ps)
    if skills:
        print("  Skills:")
        print("    • " + ", ".join(skills))


def _render_text_project(ps: ProjectSummary, collaborative: bool = False) -> None:
    print(f"\n- {ps.project_name}")
    print("  Type: Academic writing")

    if ps.summary_text:
        print(f"  Summary: {ps.summary_text}")

    skills = _extract_skills(ps)
    if skills:
        print("  Skills:")
        print("    • " + ", ".join(skills))


def _extract_skills(ps: ProjectSummary) -> List[str]:
    skills = ps.metrics.get("skills_detailed")
    if isinstance(skills, list):
        names = [s.get("skill_name") for s in skills if isinstance(s, dict) and s.get("skill_name")]
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for n in names:
            if n not in seen:
                seen.add(n)
                unique.append(n)
        return unique
    return []


def _render_aggregated_skills(summaries: List[ProjectSummary]) -> None:
    langs = set()
    frameworks = set()
    tech_skills = set()
    writing_skills = set()

    writing_skill_names = {
        "clarity", "structure", "vocabulary", "argumentation", "depth", "process",
        "planning", "research", "data_collection", "data_analysis"
    }

    for ps in summaries:
        langs.update(ps.languages or [])
        frameworks.update(ps.frameworks or [])
        skills = _extract_skills(ps)
        for s in skills:
            if s in writing_skill_names:
                writing_skills.add(s)
            else:
                tech_skills.add(s)

    print("\n=== Skills Summary ===")
    if langs:
        print(f"Languages: {', '.join(sorted(langs))}")
    if frameworks:
        print(f"Frameworks: {', '.join(sorted(frameworks))}")
    if tech_skills:
        print(f"Technical skills: {', '.join(sorted(tech_skills))}")
    if writing_skills:
        print(f"Writing skills: {', '.join(sorted(writing_skills))}")
