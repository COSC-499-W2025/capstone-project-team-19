import json
from typing import List, Dict, Any

from src.db import (
    list_resumes,
    get_resume_snapshot,
    update_resume_snapshot,  
    delete_resume_snapshot
)


def _render_snapshot(snapshot: Dict[str, Any], print_output: bool = True) -> str:
    """Render a snapshot to text; optionally print to console."""
    lines: List[str] = []

    projects = snapshot.get("projects", [])
    # Group by type/mode
    groups = {
        ("code", "individual"): "=== Code Projects (Individual) ===",
        ("code", "collaborative"): "=== Code Projects (Collaborative) ===",
        ("text", "individual"): "=== Text Projects (Individual) ===",
        ("text", "collaborative"): "=== Text Projects (Collaborative) ===",
    }

    for (ptype, pmode), header in groups.items():
        group_entries = [p for p in projects if p.get("project_type") == ptype and p.get("project_mode") == pmode]
        if not group_entries:
            continue
        lines.append("")
        lines.append(header)
        for p in group_entries:
            lines.extend(_render_project_block(p))

    agg = snapshot.get("aggregated_skills", {})
    skills_lines = []
    if agg.get("languages"):
        skills_lines.append(f"Languages: {', '.join(sorted(set(agg['languages'])))}")
    if agg.get("frameworks"):
        skills_lines.append(f"Frameworks: {', '.join(sorted(set(agg['frameworks'])))}")
    if agg.get("technical_skills"):
        skills_lines.append(f"Technical skills: {', '.join(sorted(set(agg['technical_skills'])))}")
    if agg.get("writing_skills"):
        skills_lines.append(f"Writing skills: {', '.join(sorted(set(agg['writing_skills'])))}")

    if skills_lines:
        lines.append("")
        lines.append("=== Skills Summary ===")
        lines.extend(skills_lines)

    rendered = "\n".join(lines).strip() + "\n"
    if print_output:
        print("\n" + rendered)
    return rendered


def _render_project_block(p: Dict[str, Any]) -> List[str]:
    lines = [f"\n- {p.get('project_name', 'Unnamed project')}"]

    langs = p.get("languages") or []
    fws = p.get("frameworks") or []
    if langs:
        lines.append(f"  Languages: {', '.join(sorted(set(langs)))}")
    if fws:
        lines.append(f"  Frameworks: {', '.join(sorted(set(fws)))}")

    if p.get("project_type") == "text":
        lines.append(f"  Type: {p.get('text_type', 'Text')}")
    if p.get("summary_text"):
        lines.append(f"  Summary: {p['summary_text']}")

    if p.get("project_type") == "code":
        activities = p.get("activities") or []
        if activities:
            lines.append("  Contributions:")
            for act in activities:
                top = act.get("top_file")
                top_info = f" (top: {top})" if top else ""
                lines.append(f"    • {act.get('name', 'activity')}{top_info}")
        else:
            lines.append("  Contributions: (no activity data)")
    elif p.get("project_type") == "text":
        pct = p.get("contribution_percent")
        if isinstance(pct, (int, float)):
            lines.append(f"  Contribution: {pct:.1f}% of document")

    skills = p.get("skills") or []
    if skills:
        lines.append("  Skills:")
        lines.append("    • " + ", ".join(skills))

    return lines


def refresh_saved_resumes_after_project_delete(
    conn,
    user_id: int,
    project_name: str,
) -> None:
    """
    After a project is deleted, update all saved resume snapshots to remove it.

    Behaviour:
      - If a resume snapshot *does not* contain the project: leave it as is.
      - If, after removing the project, no projects remain: delete that resume.
      - Otherwise:
          * update 'projects' list
          * recompute aggregated_skills from remaining projects
          * re-render the resume text and save back to DB
    """
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("[Resume] No saved resumes to refresh.")
        return

    updated = 0
    removed = 0
    unaffected = 0

    # Writing skill labels, taken from _aggregate_skills()
    writing_skill_labels = {
        "Clear communication",
        "Structured writing",
        "Strong vocabulary",
        "Analytical writing",
        "Critical thinking",
        "Revision & editing",
        "Planning & organization",
        "Research integration",
        "Data collection",
        "Data analysis",
    }

    for r in resumes:
        record = get_resume_snapshot(conn, user_id, r["id"])
        if not record:
            continue

        try:
            snapshot = json.loads(record["resume_json"])
        except Exception:
            print(f"[Resume] Skipping malformed resume JSON for '{record['name']}'.")
            continue

        projects = snapshot.get("projects") or []
        original_len = len(projects)
        if original_len == 0:
            unaffected += 1
            continue

        new_projects = [
            p for p in projects
            if p.get("project_name") != project_name
        ]

        if len(new_projects) == original_len:
            # This resume didn't include the deleted project.
            unaffected += 1
            continue

        if not new_projects:
            # No projects left – delete this resume snapshot entirely.
            delete_resume_snapshot(conn, user_id, record["id"])
            removed += 1
            continue

        # Rebuild aggregated skills from remaining project entries only.
        langs = set()
        frameworks = set()
        tech_skills = set()
        writing_skills = set()

        for p in new_projects:
            for lang in (p.get("languages") or []):
                langs.add(lang)
            for fw in (p.get("frameworks") or []):
                frameworks.add(fw)
            for skill in (p.get("skills") or []):
                if skill in writing_skill_labels:
                    writing_skills.add(skill)
                else:
                    tech_skills.add(skill)

        snapshot["projects"] = new_projects
        snapshot["aggregated_skills"] = {
            "languages": sorted(langs),
            "frameworks": sorted(frameworks),
            "technical_skills": sorted(tech_skills),
            "writing_skills": sorted(writing_skills),
        }

        rendered = _render_snapshot(snapshot, print_output=False)
        updated_json = json.dumps(snapshot, default=str)
        update_resume_snapshot(conn, user_id, record["id"], updated_json, rendered)
        updated += 1

    print(
        f"\n[Resume] Refreshed {updated} resume(s); "
        f"removed {removed} empty resume(s); {unaffected} unaffected."
    )
