import json

from src.db import (
    list_resumes,
    get_resume_snapshot,
    update_resume_snapshot,  
    delete_resume_snapshot
)

from src.menu.resume.helpers import (
    render_snapshot,
)

from .date_helpers import enrich_snapshot_with_dates

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

        snapshot = enrich_snapshot_with_dates(conn, user_id, snapshot)

        rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
        updated_json = json.dumps(snapshot, default=str)
        update_resume_snapshot(conn, user_id, record["id"], updated_json, rendered)
        updated += 1

    print(
        f"\n[Resume] Refreshed {updated} resume(s); "
        f"removed {removed} empty resume(s); {unaffected} unaffected."
    )

