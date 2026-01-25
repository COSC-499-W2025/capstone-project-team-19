"""
src/menu/resume/flow.py

Flow handlers for creating and viewing resume snapshots.
Separated from menu.py to keep menu wiring light.
"""

import json
from typing import Any
from datetime import datetime

from src.db import (
    get_all_user_project_summaries,
    insert_resume_snapshot,
    list_resumes,
    get_resume_snapshot,
    update_resume_snapshot,
)
from src.insights.rank_projects.rank_project_importance import collect_project_data
from .helpers import (
    load_project_summaries,
    build_resume_snapshot,
    render_snapshot,
    resolve_resume_display_name,
    resolve_resume_summary_text,
    resolve_resume_contribution_bullets,
    apply_resume_only_updates,
    enrich_snapshot_with_contributions
)
from src.export.resume_docx import export_resume_record_to_docx
from src.export.resume_pdf import export_resume_record_to_pdf
from src.services.resume_overrides import (
    update_project_manual_overrides,
    apply_manual_overrides_to_resumes,
)

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

    # NEW: freeze the "Contributed..." bullets into the snapshot JSON
    snapshot = enrich_snapshot_with_contributions(conn, user_id, snapshot)

    rendered = render_snapshot(conn, user_id, snapshot)

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


def _handle_edit_resume_wording(conn, user_id: int, username: str) -> bool:
    # Entry point for resume wording edits (resume-only vs global).
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("No saved resumes yet. Create one first.")
        return False

    print("\nSaved resumes:")
    for idx, r in enumerate(resumes, 1):
        print(f"{idx}. {r['name']} (created {r['created_at']})")

    choice = input("Select a resume to edit (number) or press Enter to cancel: ").strip()
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

    try:
        snapshot = json.loads(record["resume_json"])
    except Exception:
        print("Stored resume is corrupted or unreadable.")
        return False

    projects = snapshot.get("projects") or []
    if not projects:
        print("No projects found in this resume.")
        return False

    print("\nProjects in this resume:")
    for p_idx, p in enumerate(projects, 1):
        display = resolve_resume_display_name(p)
        summary = resolve_resume_summary_text(p)
        summary_preview = (summary[:60] + "...") if summary and len(summary) > 60 else (summary or "")
        preview = f" — {summary_preview}" if summary_preview else ""
        print(f"{p_idx}. {display}{preview}")

    proj_choice = input("Select a project to edit (number) or press Enter to cancel: ").strip()
    if not proj_choice.isdigit():
        print("Cancelled.")
        return False

    p_idx = int(proj_choice)
    if p_idx < 1 or p_idx > len(projects):
        print("Invalid selection.")
        return False

    project_entry = projects[p_idx - 1]
    project_name = project_entry.get("project_name")
    if not project_name:
        print("Selected project is missing a project name.")
        return False

    print("\nApply changes to:")
    print("1. This resume only")
    print("2. All resumes & project")
    scope_choice = input("Select scope (1-2): ").strip()
    if scope_choice not in {"1", "2"}:
        print("Cancelled.")
        return False

    sections = _prompt_edit_sections()
    if not sections:
        print("Cancelled.")
        return False

    updates = _collect_section_updates(sections, project_entry)
    if not updates:
        print("No updates provided.")
        return False

    # Resume-only updates: only touch the selected resume snapshot.
    if scope_choice == "1":
        apply_resume_only_updates(project_entry, updates)
        rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
        updated_json = json.dumps(snapshot, default=str)
        update_resume_snapshot(conn, user_id, resume_id, updated_json, rendered)
        print("[Resume] Updated wording for this resume.")
        return True

    # Global updates: persist to project_summaries, then fan out to all saved resumes.
    manual_overrides = update_project_manual_overrides(conn, user_id, project_name, updates)
    if manual_overrides is None:
        print("Unable to update project summary for global overrides.")
        return False

    apply_manual_overrides_to_resumes(
        conn,
        user_id,
        project_name,
        manual_overrides,
        updates.keys(),
        force_resume_id=resume_id,
        log_summary=True,
    )
    print("[Resume] Updated wording across resumes.")
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



def _prompt_edit_sections() -> set[str]:
    print("\nWhat would you like to edit?")
    print("1. Summary text")
    print("2. Contribution bullets")
    print("3. Display name")
    raw = input("Select one or more (e.g., 1,3) or press Enter to cancel: ").strip()
    if not raw:
        return set()
    selected: set[str] = set()
    for token in raw.replace(" ", "").split(","):
        if token == "1":
            selected.add("summary_text")
        elif token == "2":
            selected.add("contribution_bullets")
        elif token == "3":
            selected.add("display_name")
    return selected


def _collect_section_updates(sections: set[str], project_entry: dict | None = None) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if "display_name" in sections:
        display_name = input("New display name (leave blank to clear): ").strip()
        updates["display_name"] = display_name or None
    if "summary_text" in sections:
        summary_text = input("New summary text (leave blank to clear): ").strip()
        updates["summary_text"] = summary_text or None
    if "contribution_bullets" in sections:
        current_bullets: list[str] = []
        if project_entry:
            current_bullets = resolve_resume_contribution_bullets(project_entry)

        # Show current contributions if they exist
        if current_bullets:
            print("\nCurrent contributions:")
            for bullet in current_bullets:
                print(f"  • {bullet}")

            # Prompt for edit mode
            print("\nHow would you like to edit?")
            print("1. Add new bullet points (keep existing and append new ones)")
            print("2. Replace all (delete existing and write new bullet points)")
            mode = input("Select (1-2): ").strip()

            if mode == "1":
                print("\nEnter additional contribution bullets (one per line). Press Enter on a blank line to finish.")
                new_bullets: list[str] = []
                while True:
                    line = input("> ").strip()
                    if not line:
                        break
                    new_bullets.append(line)
                # Append new bullets to existing
                updates["contribution_bullets"] = current_bullets + new_bullets if new_bullets else None
            else:
                # Rewrite mode (mode == "2" or invalid input defaults to rewrite)
                print("\nEnter contribution bullets (one per line). Press Enter on a blank line to finish.")
                bullets: list[str] = []
                while True:
                    line = input("> ").strip()
                    if not line:
                        break
                    bullets.append(line)
                updates["contribution_bullets"] = bullets or None
        else:
            # No existing contributions - use original flow
            print("Enter contribution bullets (one per line). Press Enter on a blank line to finish.")
            bullets: list[str] = []
            while True:
                line = input("> ").strip()
                if not line:
                    break
                bullets.append(line)
            updates["contribution_bullets"] = bullets or None
    return updates


def _handle_export_resume_pdf(conn, user_id: int, username: str) -> bool:
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("No saved resumes yet. Create one first.")
        return False

    print("\nSaved resumes:")
    for idx, r in enumerate(resumes, 1):
        print(f"{idx}. {r['name']} (created {r['created_at']})")

    choice = input("Select a resume to export as PDF (number) or press Enter to cancel: ").strip()
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

    out_file = export_resume_record_to_pdf(username=username, record=record, out_dir="./out")
    print(f"\nSaving resume to {out_file} ...")
    print("✓ Export complete.\n")
    return True
