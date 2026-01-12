"""
src/menu/resume/menu.py

Menu option for creating and viewing resume snapshots.
Delegates heavy lifting to flow.py.
"""

from .flow import _handle_create_resume, _handle_view_existing_resume, _handle_export_resume_docx


def view_resume_items(conn, user_id: int, username: str):
    """
    Prompt to create a new resume snapshot or view an existing one.
    """
    while True:
        print("\nResume options:")
        print("")
        print("1. Create a new resume from current projects")
        print("2. View an existing resume snapshot")
        print("3. Export a resume snapshot to Word (.docx)")
        print("4. Back to main menu")
        choice = input("Select an option (1-4): ").strip()

        if choice == "1":
            _handle_create_resume(conn, user_id, username)
            print("")
            continue
        elif choice == "2":
            handled = _handle_view_existing_resume(conn, user_id)
            if handled:
                print("")
                continue
            # otherwise loop back to resume menu
        elif choice == "3":
            handled = _handle_export_resume_docx(conn, user_id, username)
            if handled:
                print("")
                continue
        elif choice == "4":
            print("")
            return
        else:
            print("Invalid choice, please enter 1, 2, 3, or 4.")
