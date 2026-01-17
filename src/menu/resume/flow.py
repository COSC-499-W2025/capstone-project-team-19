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
    get_project_summary_by_name,
    update_project_summary_json,
)
from src.insights.rank_projects.rank_project_importance import collect_project_data
from .helpers import (
    load_project_summaries,
    build_resume_snapshot,
    render_snapshot,
    resolve_resume_display_name,
    resolve_resume_summary_text,
    resume_only_override_fields,
    apply_resume_only_updates,
    enrich_snapshot_with_contributions
)
from src.export.resume_docx import export_resume_record_to_docx
from src.export.resume_pdf import export_resume_record_to_pdf

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

    updates = _collect_section_updates(sections)
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
    manual_overrides = _update_project_manual_overrides(conn, user_id, project_name, updates)
    if manual_overrides is None:
        print("Unable to update project summary for global overrides.")
        return False

    _apply_manual_overrides_to_resumes(
        conn,
        user_id,
        project_name,
        manual_overrides,
        updates.keys(),
        force_resume_id=resume_id,
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


def _collect_section_updates(sections: set[str]) -> dict[str, Any]:
    updates: dict[str, Any] = {}
    if "display_name" in sections:
        display_name = input("New display name (leave blank to clear): ").strip()
        updates["display_name"] = display_name or None
    if "summary_text" in sections:
        summary_text = input("New summary text (leave blank to clear): ").strip()
        updates["summary_text"] = summary_text or None
    if "contribution_bullets" in sections:
        print("Enter contribution bullets (one per line). Press Enter on a blank line to finish.")
        bullets: list[str] = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            bullets.append(line)
        updates["contribution_bullets"] = bullets or None
    return updates


def _update_project_manual_overrides(conn, user_id: int, project_name: str, updates: dict[str, Any]) -> dict[str, Any] | None:
    summary_row = get_project_summary_by_name(conn, user_id, project_name)
    if not summary_row:
        return None

    try:
        summary_dict = json.loads(summary_row["summary_json"])
    except Exception:
        return None

    # Keep manual overrides on the project summary (shared by resume + portfolio).
    overrides = summary_dict.get("manual_overrides") or {}
    if not isinstance(overrides, dict):
        overrides = {}

    for key, value in updates.items():
        if value:
            overrides[key] = value
        else:
            overrides.pop(key, None)

    if overrides:
        summary_dict["manual_overrides"] = overrides
    else:
        summary_dict.pop("manual_overrides", None)

    updated = update_project_summary_json(conn, user_id, project_name, json.dumps(summary_dict))
    if not updated:
        return None
    return overrides


def _apply_manual_overrides_to_resumes(
    conn,
    user_id: int,
    project_name: str,
    overrides: dict[str, Any],
    fields: set[str],
    force_resume_id: int | None = None,
) -> None:
    # Walk all saved resumes and apply the global overrides per matching project.
    resumes = list_resumes(conn, user_id)
    updated = 0
    skipped_fields = 0

    for r in resumes:
        record = get_resume_snapshot(conn, user_id, r["id"])
        if not record:
            continue
        try:
            snapshot = json.loads(record["resume_json"])
        except Exception:
            continue

        projects = snapshot.get("projects") or []
        changed = False
        for entry in projects:
            if entry.get("project_name") != project_name:
                continue
            resume_only_fields = resume_only_override_fields(entry)
            force_update = force_resume_id == r["id"]
            # If this is the selected resume, clear resume-only overrides so global applies.
            if force_update and resume_only_fields:
                clear_updates = {field: None for field in fields}
                apply_resume_only_updates(entry, clear_updates)
                resume_only_fields = resume_only_override_fields(entry)

            if "display_name" in fields:
                if "display_name" in resume_only_fields and not force_update:
                    # Respect resume-only overrides on other resumes (skip this field).
                    skipped_fields += 1
                else:
                    if overrides.get("display_name"):
                        entry["manual_display_name"] = overrides["display_name"]
                    else:
                        entry.pop("manual_display_name", None)
                    changed = True
            if "summary_text" in fields:
                if "summary_text" in resume_only_fields and not force_update:
                    # Respect resume-only overrides on other resumes (skip this field).
                    skipped_fields += 1
                else:
                    if overrides.get("summary_text"):
                        entry["manual_summary_text"] = overrides["summary_text"]
                    else:
                        entry.pop("manual_summary_text", None)
                    changed = True
            if "contribution_bullets" in fields:
                if "contribution_bullets" in resume_only_fields and not force_update:
                    # Respect resume-only overrides on other resumes (skip this field).
                    skipped_fields += 1
                else:
                    if overrides.get("contribution_bullets"):
                        entry["manual_contribution_bullets"] = overrides["contribution_bullets"]
                    else:
                        entry.pop("manual_contribution_bullets", None)
                    changed = True

        if changed:
            # Re-render and persist the updated snapshot.
            rendered = render_snapshot(conn, user_id, snapshot, print_output=False)
            updated_json = json.dumps(snapshot, default=str)
            update_resume_snapshot(conn, user_id, r["id"], updated_json, rendered)
            updated += 1

    if updated or skipped_fields:
        print(f"[Resume] Updated {updated} resume(s); skipped {skipped_fields} field update(s) due to resume-only overrides.")

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
