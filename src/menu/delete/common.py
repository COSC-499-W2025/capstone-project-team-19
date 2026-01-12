from src.menu.portfolio import view_portfolio_items
from src.menu.resume.flow import _handle_create_resume


def post_delete_next_steps(conn, user_id: int, username: str) -> None:
    while True:
        print("\nWhat next?")
        print("1. View updated portfolio")
        print("2. Create a new resume now")
        print("3. Return to main menu")

        choice = input("Select (1-3): ").strip()
        if choice == "1":
            view_portfolio_items(conn, user_id, username)
            return
        elif choice == "2":
            _handle_create_resume(conn, user_id, username)
            return
        elif choice == "3" or choice.lower() in {"q", "quit"}:
            return
        print("Please enter 1, 2, or 3.")
