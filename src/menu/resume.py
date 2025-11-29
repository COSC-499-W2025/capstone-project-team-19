"""
src/menu/resume.py

Menu option for creating and viewing resume snapshots.
"""

import json
from datetime import datetime
from typing import List, Dict, Any

from src.db import (
    get_all_user_project_summaries,
    insert_resume_snapshot,
    list_resumes,
    get_resume_snapshot,
)
from src.models.project_summary import ProjectSummary


def view_resume_items(conn, user_id: int, username: str):
    """
    Prompt to create a new resume snapshot or view an existing one.
    """
    while True:
        print("\nResume options:")
        print("1. Create a new resume from current projects")
        print("2. View an existing resume snapshot")
        print("3. Back to main menu")
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            _handle_create_resume(conn, user_id, username)
            return
        elif choice == "2":
            _handle_view_existing_resume(conn, user_id)
            return
        elif choice == "3":
            return
        else:
            print("Invalid choice, please enter 1, 2, or 3.")


def _handle_create_resume(conn, user_id: int, username: str):
    summaries = _load_project_summaries(conn, user_id)
    if not summaries:
        print("No project summaries available. Run an analysis first.")
        return

    snapshot = _build_resume_snapshot(summaries)
    rendered = _render_snapshot(snapshot)

    default_name = f"Resume {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    name = input(f"Enter a name for this resume [{default_name}]: ").strip() or default_name

    resume_json = json.dumps(snapshot, default=str)
    insert_resume_snapshot(conn, user_id, name, resume_json, rendered)
    print(f"\n[Resume] Saved snapshot '{name}'.")


def _handle_view_existing_resume(conn, user_id: int):
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("No saved resumes yet. Create one first.")
        return

    print("\nSaved resumes:")
    for idx, r in enumerate(resumes, 1):
        print(f"{idx}. {r['name']} (created {r['created_at']})")

    choice = input("Select a resume to view (number) or press Enter to cancel: ").strip()
    if not choice.isdigit():
        print("Cancelled.")
        return

    idx = int(choice)
    if idx < 1 or idx > len(resumes):
        print("Invalid selection.")
        return

    resume_id = resumes[idx - 1]["id"]
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        print("Unable to load the selected resume.")
        return

    # Prefer stored rendered text; fall back to rendering from stored JSON.
    if record.get("rendered_text"):
        print("\n" + record["rendered_text"])
    else:
        try:
            snapshot = json.loads(record["resume_json"])
            _render_snapshot(snapshot, print_output=True)
        except Exception:
            print("Stored resume is corrupted or unreadable.")


def _load_project_summaries(conn, user_id: int) -> List[ProjectSummary]:
    """Fetch and deserialize all saved project summaries for the user."""
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


def _build_resume_snapshot(summaries: List[ProjectSummary]) -> Dict[str, Any]:
    """Build a structured snapshot of resume data from project summaries."""
    projects = []
    for ps in summaries:
        entry: Dict[str, Any] = {
            "project_name": ps.project_name,
            "project_type": ps.project_type,
            "project_mode": ps.project_mode,
            "languages": ps.languages or [],
            "frameworks": ps.frameworks or [],
            "summary_text": ps.summary_text,
            "skills": _extract_skills(ps),
        }

        if ps.project_type == "text":
            entry["text_type"] = "Academic writing"
            if ps.project_mode == "collaborative":
                text_collab = ps.contributions.get("text_collab")
                if isinstance(text_collab, dict):
                    pct = text_collab.get("percent_of_document")
                    if isinstance(pct, (int, float)):
                        entry["contribution_percent"] = pct
                    collab_skills = text_collab.get("skills")
                    if isinstance(collab_skills, list) and collab_skills:
                        entry["skills"] = collab_skills
        else:  # code
            entry["activities"] = _extract_activity(ps)

        projects.append(entry)

    agg = _aggregate_skills(summaries)
    return {"projects": projects, "aggregated_skills": agg}


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


def _extract_activity(ps: ProjectSummary) -> List[Dict[str, Any]]:
    activity = None
    if ps.project_mode == "collaborative":
        activity = ps.contributions.get("activity_type")
    activity = activity or ps.metrics.get("activity_type")
    if not isinstance(activity, dict):
        return []

    items = []
    for k, v in activity.items():
        top_file = v.get("top_file") or v.get("top_file_overall")
        items.append({"name": k, "top_file": top_file})
    return items


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


def _aggregate_skills(summaries: List[ProjectSummary]) -> Dict[str, List[str]]:
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

    return {
        "languages": sorted(langs),
        "frameworks": sorted(frameworks),
        "technical_skills": sorted(tech_skills),
        "writing_skills": sorted(writing_skills),
    }
