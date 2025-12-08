"""
src/menu/resume/flow.py

Flow handlers for creating and viewing resume snapshots.
Separated from menu.py to keep menu wiring light.
"""

import json
from datetime import datetime

from src.db import (
    get_all_user_project_summaries,
    insert_resume_snapshot,
    list_resumes,
    get_resume_snapshot,
)
from src.insights.rank_projects.rank_project_importance import collect_project_data
from .helpers import load_project_summaries, build_resume_snapshot, render_snapshot


def _handle_create_resume(conn, user_id: int, username: str):
    summaries = load_project_summaries(conn, user_id, get_all_user_project_summaries)
    if not summaries:
        print("No project summaries available. Run an analysis first.")
        return

    # Rank projects and select top 5 by score
    ranked = collect_project_data(conn, user_id)
    top_names = [name for name, _score in ranked[:5]]
    if top_names:
        summaries = [s for s in summaries if s.project_name in top_names]
        print(f"[Resume] Using top {len(summaries)} ranked projects: {', '.join(top_names)}")

    snapshot = build_resume_snapshot(summaries)
    rendered = render_snapshot(snapshot)

    default_name = f"Resume {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    name = input(f"Enter a name for this resume [{default_name}]: ").strip() or default_name

    resume_json = json.dumps(snapshot, default=str)
    insert_resume_snapshot(conn, user_id, name, resume_json, rendered)
    print(f"\n[Resume] Saved snapshot '{name}'.")


def _handle_view_existing_resume(conn, user_id: int) -> bool:
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("No saved resumes yet. Create one first.")
        return False

    print("\nSaved resumes:")
    for idx, r in enumerate(resumes, 1):
        print(f"{idx}. {r['name']} (created {r['created_at']})")

    choice = input("Select a resume to view (number) or press Enter to cancel: ").strip()
    if not choice.isdigit():
        print("Cancelled.")
        return False

    idx = int(choice)
    if idx < 1 or idx > len(resumes):
        print("Invalid selection.")
        return False

    resume_id = resumes[idx - 1]["id"]
    record = get_resume_snapshot(conn, user_id, resume_id)
    if not record:
        print("Unable to load the selected resume.")
        return False

    # Prefer stored rendered text; fall back to rendering from stored JSON.
    if record.get("rendered_text"):
        print("\n" + record["rendered_text"])
    else:
        try:
            snapshot = json.loads(record["resume_json"])
            render_snapshot(snapshot, print_output=True)
        except Exception:
            print("Stored resume is corrupted or unreadable.")
            return False

    return True
