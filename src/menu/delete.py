from __future__ import annotations

from typing import Optional

from src.db import (
    get_project_summaries_list,
    list_resumes,
    delete_resume_snapshot,
    delete_project_everywhere,
)
from src.menu.resume import (
    refresh_saved_resumes_after_project_delete,
    create_resume_from_current_projects,
)
from src.menu.portfolio import view_portfolio_items


def delete_old_insights(conn, user_id: int, username: str) -> None:
    """
    Entry point for the 'Delete old insights' menu.

    Options:
      1) Delete a project (with choice of how to handle saved resumes)
      2) Delete a saved resume
      3) Back to main menu
    """
    while True:
        print("\n" + "=" * 60)
        print("DELETE OLD INSIGHTS")
        print("=" * 60)
        print("1. Delete a project")
        print("2. Delete a saved resume")
        print("3. Back to main menu")

        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            _handle_delete_project(conn, user_id, username)
        elif choice == "2":
            _handle_delete_resume(conn, user_id, username)
        elif choice == "3" or choice.lower() in {"q", "quit"}:
            return
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")


# --- Project deletion -------------------------------------------------


def _select_project(
    conn,
    user_id: int,
    username: str,
) -> Optional[str]:
    """
    List all project summaries and let the user pick one to delete.

    Returns the selected project_name, or None if cancelled.
    """
    summaries = get_project_summaries_list(conn, user_id)

    if not summaries:
        print(f"\nNo project summaries found for {username}.")
        print("You haven't analyzed any projects yet.")
        input("\nPress Enter to return...")
        return None

    print(f"\n{username}'s Projects:\n")
    for idx, summary in enumerate(summaries, start=1):
        project_type = summary.get("project_type") or "unknown"
        project_mode = summary.get("project_mode") or "unknown"
        created_at = summary.get("created_at")
        print(
            f"{idx}. {summary['project_name']} "
            f"({project_mode} {project_type} project, analyzed: {created_at})"
        )

    print("0. Cancel")

    while True:
        raw = input("\nSelect a project to delete (0 to cancel): ").strip()
        if raw in {"0", "", "q", "Q"}:
            return None
        if not raw.isdigit():
            print("Please enter a number from the list, or 0 to cancel.")
            continue

        idx = int(raw)
        if 1 <= idx <= len(summaries):
            return summaries[idx - 1]["project_name"]

        print(f"Invalid selection. Enter a number between 0 and {len(summaries)}, or 0 to cancel.")


def _handle_delete_project(conn, user_id: int, username: str) -> None:
    project_name = _select_project(conn, user_id, username)
    if not project_name:
        return

    print("\nYou are about to permanently delete all stored data for:")
    print(f"  • Project: {project_name}")
    print("This includes:")
    print("  - File listings and project classifications")
    print("  - Text and code analysis metrics")
    print("  - Project summaries and skills")
    print("  - Linked GitHub/Drive data for this project")
    print("")
    confirm = input("Type DELETE to confirm, or press Enter to cancel: ").strip()
    if confirm != "DELETE":
        print("Cancelled. Project was not deleted.")
        return

    print("\nHow should we handle your *saved resumes* after deleting this project?\n")
    print("1. Delete project everywhere AND refresh saved resumes")
    print("   (remove this project from each resume snapshot)")
    print("2. Delete project everywhere BUT keep all saved resumes as they are")
    print("   (old resumes may still mention this project)")
    print("3. Cancel")

    refresh_resumes = False
    while True:
        choice = input("Select an option (1-3): ").strip()
        if choice == "1":
            refresh_resumes = True
            break
        elif choice == "2":
            refresh_resumes = False
            break
        elif choice == "3":
            print("Cancelled. Project was not deleted.")
            return
        else:
            print("Please enter 1, 2, or 3.")

    # Hard delete across all tables
    delete_project_everywhere(conn, user_id, project_name)
    print(f"\n[Delete] Project '{project_name}' has been deleted from all analysis and integration tables.")

    if refresh_resumes:
        refresh_saved_resumes_after_project_delete(conn, user_id, project_name)

    _post_delete_next_steps(conn, user_id, username)


# --- Resume deletion --------------------------------------------------


def _handle_delete_resume(conn, user_id: int, username: str) -> None:
    resumes = list_resumes(conn, user_id)
    if not resumes:
        print("\nNo saved resumes found.")
        input("Press Enter to return...")
        return

    print("\nSaved resumes:")
    for idx, r in enumerate(resumes, start=1):
        print(f"{idx}. {r['name']} (created {r['created_at']})")
    print("0. Cancel")

    while True:
        raw = input("Select a resume to delete (0 to cancel): ").strip()
        if raw in {"0", "", "q", "Q"}:
            return
        if not raw.isdigit():
            print("Please enter a number from the list, or 0 to cancel.")
            continue

        idx = int(raw)
        if 1 <= idx <= len(resumes):
            selected = resumes[idx - 1]
            break

        print(f"Invalid selection. Enter a number between 0 and {len(resumes)}, or 0 to cancel.")

    resume_name = selected["name"]
    resume_id = selected["id"]

    confirm = input(
        f"\nType DELETE to permanently delete resume '{resume_name}', "
        "or press Enter to cancel: "
    ).strip()
    if confirm != "DELETE":
        print("Cancelled. Resume was not deleted.")
        return

    delete_resume_snapshot(conn, user_id, resume_id)
    print(f"\n[Delete] Removed resume snapshot '{resume_name}'.")

    _post_delete_next_steps(conn, user_id, username)


# --- Post-action menu -------------------------------------------------


def _post_delete_next_steps(conn, user_id: int, username: str) -> None:
    """
    Common follow-up menu after either project or resume deletion.
    """
    while True:
        print("\nWhat next?")
        print("1. View updated portfolio now")
        print("2. Create a new resume now")
        print("3. Return to main menu")

        choice = input("Select an option (1-3): ").strip()
        if choice == "1":
            view_portfolio_items(conn, user_id, username)
            return
        elif choice == "2":
            create_resume_from_current_projects(conn, user_id, username)
            return
        elif choice == "3" or choice.lower() in {"q", "quit"}:
            return
        else:
            print("Please enter 1, 2, or 3.")

