from src.db import list_resumes, delete_resume_snapshot
from src.menu.delete.common import post_delete_next_steps


def handle_delete_resume(conn, user_id: int, username: str) -> None:
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
        if raw.isdigit() and 1 <= int(raw) <= len(resumes):
            selected = resumes[int(raw) - 1]
            break
        print("Invalid selection.")

    name = selected["name"]
    resume_id = selected["id"]

    confirm = input(f"\nType DELETE to permanently delete '{name}': ").strip()
    if confirm != "DELETE":
        print("Cancelled.")
        return

    delete_resume_snapshot(conn, user_id, resume_id)
    print(f"\n[Delete] Resume '{name}' removed.")

    post_delete_next_steps(conn, user_id, username)
