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
from src.export.resume_docx import export_resume_record_to_docx

def _handle_create_resume(conn, user_id: int, username: str):
    summaries = load_project_summaries(conn, user_id, get_all_user_project_summaries)
    if not summaries:
        print("No project summaries available. Run an analysis first.")
        return

    # Rank projects to show user
    ranked = collect_project_data(conn, user_id)
    
    if not ranked:
        print("No projects available to rank.")
        return
    
    # Create a dict for quick lookup: project_name -> score
    ranked_dict = {name: score for name, score in ranked}
    
    # Show ranked projects with scores
    print("\nAvailable projects (ranked by importance):")
    print("-" * 60)
    for idx, (project_name, score) in enumerate(ranked, start=1):
        # Find matching summary to show type/mode
        summary = next((s for s in summaries if s.project_name == project_name), None)
        if summary:
            type_mode = f"({summary.project_mode} {summary.project_type})"
            print(f"{idx:2d}. {project_name:<30} {type_mode:<25} Score: {score:.3f}")
        else:
            print(f"{idx:2d}. {project_name:<30} {'':<25} Score: {score:.3f}")
    
    print("\nSelect  projects to include (maximum 5 projects):")
    print("  • Enter numbers separated by commas (e.g., 1,3,5)")
    print("  • Or press Enter to use top 5 ranked projects")
    
    choice = input("\nYour selection: ").strip()
    
    if not choice:
        # Default: top 5
        top_names = [name for name, _score in ranked[:5]]
        selected_summaries = [s for s in summaries if s.project_name in top_names]
        # Sort by ranking order (highest score first)
        selected_summaries.sort(
            key=lambda s: ranked_dict.get(s.project_name, 0.0),
            reverse=True
        )
        print(f"\n[Resume] Using top {len(selected_summaries)} ranked projects: {', '.join(top_names)}")
    else:
        # Parse user selection (handle comma-separated numbers)
        selected_indices = set()
        for token in choice.replace(" ", "").split(","):
            if token.isdigit():
                idx = int(token)
                if 1 <= idx <= len(ranked):
                    selected_indices.add(idx)
        
        if not selected_indices:
            print("No valid selections. Using top 5 ranked projects.")
            top_names = [name for name, _score in ranked[:5]]
            selected_summaries = [s for s in summaries if s.project_name in top_names]
            # Sort by ranking order
            selected_summaries.sort(
                key=lambda s: ranked_dict.get(s.project_name, 0.0),
                reverse=True
            )
        else:
            # Limit to 5 projects maximum
            MAX_PROJECTS = 5
            if len(selected_indices) > MAX_PROJECTS:
                print(f"\n[Warning] You selected {len(selected_indices)} projects. Maximum is {MAX_PROJECTS}.")
                print(f"Using the first {MAX_PROJECTS} projects by ranking order.")
                # Sort indices by their ranking order (lower index = higher rank)
                sorted_indices = sorted(selected_indices)
                selected_indices = set(sorted_indices[:MAX_PROJECTS])
            
            selected_names = [ranked[i-1][0] for i in sorted(selected_indices)]
            selected_summaries = [s for s in summaries if s.project_name in selected_names]
            # Sort by ranking order (highest score first)
            selected_summaries.sort(
                key=lambda s: ranked_dict.get(s.project_name, 0.0),
                reverse=True
            )
            print(f"\n[Resume] Using {len(selected_summaries)} selected projects: {', '.join(selected_names)}")
    
    snapshot = build_resume_snapshot(selected_summaries)
    rendered = render_snapshot(conn, user_id, snapshot, print_output=False)

    default_name = f"Resume {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    name = input(f"\nEnter a name for this resume [{default_name}]: ").strip() or default_name

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

    # Use stored rendered text, fall back JSON
    if record.get("rendered_text"):
        print("\n" + record["rendered_text"])
    else:
        try:
            snapshot = json.loads(record["resume_json"])
            render_snapshot(conn, user_id, snapshot, print_output=True)
        except Exception:
            print("Stored resume is corrupted or unreadable.")
            return False

    return True

def _handle_export_resume_docx(conn, user_id: int, username: str) -> bool:
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("No saved resumes yet. Create one first.")
        return False

    print("\nSaved resumes:")
    for idx, r in enumerate(resumes, 1):
        print(f"{idx}. {r['name']} (created {r['created_at']})")

    choice = input("Select a resume to export (number) or press Enter to cancel: ").strip()
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

    out_file = export_resume_record_to_docx(username=username, record=record, out_dir="./out")
    print(f"\nSaving resume to {out_file} ...")
    print("✓ Export complete.\n")
    return True
