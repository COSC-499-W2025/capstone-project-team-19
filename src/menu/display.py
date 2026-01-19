"""
src/menu/display.py

Main menu display functionality.
"""


def show_start_menu(username: str) -> int:
    """
    Display the main menu and return user's choice.
    """
    print(f"\nWelcome, {username}!")
    print("1. Analyze new project")
    print("2. View old project summaries")
    print("3. View resume items")
    print("4. View portfolio items")
    print("5. View project feedback")
    print("6. Delete old insights")
    print("7. View all projects ranked")
    print("8. View chronological skills")
    print("9. Edit project dates")
    print("10. View all projects")
    print("11. Exit")

    while True:
        choice = input("\nPlease select an option (1-11): ").strip()
        if choice in {"1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11"}:
            return int(choice)
        print("Invalid choice. Please enter a number between 1 and 11.")

