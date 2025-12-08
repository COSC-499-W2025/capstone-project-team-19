from typing import Optional

from src.db import (
    get_project_summaries_list,
    delete_project_everywhere,
)
from src.menu.resume.resume import refresh_saved_resumes_after_project_delete
from src.menu.delete.common import post_delete_next_steps


def _select_project(conn, user_id: int, username: str) -> Optional[str]:
    summaries = get_project_summaries_list(conn, user_id)

    if not summaries:
        print(f"\nNo project summaries found for {username}.")
        input("Press Enter to return...")
        return None

    print(f"\n{username}'s Projects:\n")
    for idx, s in enumerate(summaries, start=1):
        print(f"{idx}. {s['project_name']} ({s.get('project_mode')} {s.get('project_type')})")

    print("0. Cancel")

    while True:
        raw = input("\nSelect a project to delete (0 to cancel): ").strip()
        if raw in {"0", "", "q", "Q"}:
            return None
        if raw.isdigit() and 1 <= int(raw) <= len(summaries):
            return summaries[int(raw) - 1]["project_name"]
        print("Invalid selection.")


def handle_delete_project(conn, user_id: int, username: str) -> None:
    project_name = _select_project(conn, user_id, username)
    if not project_name:
        return

    print("\nYou are about to permanently delete all stored data for:")
    print(f"  • Project: {project_name}")
    confirm = input("Type DELETE to confirm: ").strip()
    if confirm != "DELETE":
        print("Cancelled.")
        return

    print("\nHow should we handle your saved resumes?\n")
    print("1. Delete project everywhere AND refresh saved resumes")
    print("2. Delete project everywhere BUT keep saved resumes unchanged")
    print("3. Cancel")

    refresh_resumes = None
    while True:
        choice = input("Select (1-3): ").strip()
        if choice == "1":
            refresh_resumes = True
            break
        elif choice == "2":
            refresh_resumes = False
            break
        elif choice == "3":
            print("Cancelled.")
            return
        print("Please enter 1, 2, or 3.")

    # Hard delete across all tables
    delete_project_everywhere(conn, user_id, project_name)
    print(f"\n[Delete] Project '{project_name}' removed from all tables.")

    if refresh_resumes:
        refresh_saved_resumes_after_project_delete(conn, user_id, project_name)

    post_delete_next_steps(conn, user_id, username)
