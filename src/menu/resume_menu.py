"""
src/menu/resume_menu.py

Menu option for creating and viewing resume snapshots.
Delegates heavy lifting to resume_flow.py.
"""

from .resume_flow import _handle_create_resume, _handle_view_existing_resume


def view_resume_items(conn, user_id: int, username: str):
    """
    Prompt to create a new resume snapshot or view an existing one.
    """
    while True:
        print("\nResume options:")
        print("1. Create a new resume from current projects")
        print("2. View an existing resume snapshot")
        print("3. Back to main menu")
        choice = input("Select an option (1-3): ").strip()

        if choice == "1":
            _handle_create_resume(conn, user_id, username)
            print("")
            return
        elif choice == "2":
            handled = _handle_view_existing_resume(conn, user_id)
            if handled:
                print("")
                return
            # otherwise loop back to resume menu
        elif choice == "3":
            print("")
            return
        else:
            print("Invalid choice, please enter 1, 2, or 3.")
