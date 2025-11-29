"""
src/menu/display.py

Main menu display functionality.
"""


def show_start_menu(username: str) -> int:
    """
    Display the main menu and return user's choice.
    """
    print(f"Welcome, {username}!")
    print("1. Analyze new project")
    print("2. View old project summaries")
    print("3. View resume items")
    print("4. View portfolio items")
    print("5. Delete old insights")
    print("8. View all projects (chronological list)")
    print("6. Exit")

    while True:
        choice = input("\nPlease select an option (1-6): ").strip()
        if choice in {"1", "2", "3", "4", "5", "6"}:
            return int(choice)
        print("Invalid choice. Please enter a number between 1 and 6.")
