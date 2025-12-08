from src.menu.delete.delete_project import handle_delete_project
from src.menu.delete.delete_resume import handle_delete_resume


def delete_old_insights(conn, user_id: int, username: str) -> None:
    """
    Entry point for delete-menu:
      1) Delete a project
      2) Delete a saved resume
      3) Back to main
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
            handle_delete_project(conn, user_id, username)
        elif choice == "2":
            handle_delete_resume(conn, user_id, username)
        elif choice == "3" or choice.lower() in {"q", "quit"}:
            return
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
