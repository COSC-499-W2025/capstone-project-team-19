"""
src/menu/project_dates.py

Menu for editing project dates (affects chronological skills and portfolio items).
"""

from datetime import datetime
from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import (
    get_project_dates,
    set_project_dates,
    clear_project_dates,
    clear_all_project_dates,
    get_all_manual_dates,
    get_project_summary_by_name,
    get_text_duration,
    get_code_individual_duration,
    get_code_collaborative_duration,
)

def is_valid_date(date_str: str) -> bool:
    """Validate date string is in YYYY-MM-DD format with valid month and day."""
    if len(date_str) != 10:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def prompt_for_date(prompt: str, current_value: str | None) -> str | None:
    """Prompt user for a valid date, looping until valid input or skip."""
    while True:
        date_input = input(prompt).strip()

        if not date_input:
            return current_value

        if not is_valid_date(date_input):
            print("  Invalid date. Use YYYY-MM-DD with valid month (1-12) and day.")
            print("  Press Enter to skip or try again.")
            continue

        # Check for future date
        entered_date = datetime.strptime(date_input, "%Y-%m-%d")
        if entered_date > datetime.now():
            print("  Date cannot be in the future.")
            print("  Press Enter to skip or try again.")
            continue

        return date_input


def edit_project_dates_menu(conn, user_id: int, username: str) -> None:
    while True:
        print()
        print("1. View all projects with dates")
        print("2. Set dates for specific project")
        print("3. Clear dates for specific project (revert to automatic)")
        print("4. Reset all to automatic dates")
        print("5. Return to main menu")

        choice = input("\nPlease select an option (1-5): ").strip()

        if choice == "1":
            view_all_projects_with_dates(conn, user_id, username)
        elif choice == "2":
            set_project_date(conn, user_id)
        elif choice == "3":
            clear_specific_project_dates(conn, user_id)
        elif choice == "4":
            reset_all_dates_to_auto(conn, user_id)
        elif choice == "5":
            return None
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")


def view_all_projects_with_dates(conn, user_id, username) -> None:
    """Display all projects with their dates (manual or automatic)."""
    try:
        # Get all projects
        project_scores = collect_project_data(conn, user_id)

        if not project_scores:
            print(f"\n{'='*90}")
            print("No projects found. Please analyze some projects first.")
            print(f"{'='*90}\n")
            return

        # Get manual dates
        manual_dates_dict = {name: (start, end) for name, start, end in get_all_manual_dates(conn, user_id)}

        print(f"\n{'='*90}\n")
        print(f"Project Dates for {username}")
        print(f"\n{'='*90}\n")
        print(f"Found {len(project_scores)} project(s):\n")
        print(f"{'#':<4} {'Project Name':<40} {'Start Date':<13} {'End Date':<13} {'Source':<8}")
        print("-" * 90)

        for idx, (project_name, _) in enumerate(project_scores, start=1):
            # Get summary to determine dates
            summary_row = get_project_summary_by_name(conn, user_id, project_name)

            # Check for manual dates first
            if project_name in manual_dates_dict:
                start, end = manual_dates_dict[project_name]
                start_display = start[:10] if start else "N/A"
                end_display = end[:10] if end else "N/A"
                source = "MANUAL"
            else:
                # Try to get automatic dates from database
                start_display, end_display = get_automatic_dates_from_summary(conn, user_id, project_name, summary_row)
                source = "AUTO"

            # Truncate long project names
            display_name = project_name[:37] + "..." if len(project_name) > 40 else project_name

            print(f"{idx:<4} {display_name:<40} {start_display:<13} {end_display:<13} {source:<8}")

        print(f"\n{'='*90}\n")

    except Exception as e:
        print(f"Error displaying project dates: {e}")
        print(f"{'='*90}\n")


def get_automatic_dates_from_summary(conn, user_id, project_name, summary_row):
    """Extract automatic dates from database (not from JSON summary)."""
    if not summary_row:
        return "N/A", "N/A"

    project_type = summary_row.get('project_type', 'unknown')
    project_mode = summary_row.get('project_mode', 'individual')

    # For text projects - use get_text_duration
    if project_type == 'text':
        duration = get_text_duration(conn, user_id, project_name)
        if duration:
            start, end = duration
            return start[:10] if start else "N/A", end[:10] if end else "N/A"

    # For code projects - use appropriate function based on mode
    elif project_type == 'code':
        if project_mode == 'collaborative':
            duration = get_code_collaborative_duration(conn, user_id, project_name)
        else:
            duration = get_code_individual_duration(conn, user_id, project_name)

        if duration:
            start, end = duration
            return start[:10] if start else "N/A", end[:10] if end else "N/A"

    return "N/A", "N/A"


def set_project_date(conn, user_id):
    """Set dates for a specific project."""
    # Show projects
    projects = collect_project_data(conn, user_id)

    if not projects:
        print("\nNo projects found.")
        return

    print(f"\n{'='*90}")
    print("Available Projects:")
    print(f"{'='*90}")

    for idx, (project_name, _) in enumerate(projects, start=1):
        # Get current dates
        manual_dates = get_project_dates(conn, user_id, project_name)
        if manual_dates:
            start, end = manual_dates
            status = f"[Manual: {start or 'N/A'} to {end or 'N/A'}]"
        else:
            status = "[Auto]"

        print(f"  {idx}. {project_name} {status}")

    print(f"{'='*90}")

    try:
        project_idx = int(input("\nEnter project number: ").strip()) - 1

        if project_idx < 0 or project_idx >= len(projects):
            print("Invalid project number.")
            return

        project_name = projects[project_idx][0]

        print(f"\nSetting dates for: {project_name}")
        print("Enter dates in YYYY-MM-DD format, or press Enter to skip/keep current.")

        # Get current manual dates
        current_dates = get_project_dates(conn, user_id, project_name)
        current_start = current_dates[0] if current_dates else None
        current_end = current_dates[1] if current_dates else None

        start_date = prompt_for_date("Start date (YYYY-MM-DD or Enter to skip): ", current_start)
        end_date = prompt_for_date("End date (YYYY-MM-DD or Enter to skip): ", current_end)

        # Check if there's anything to update
        if not start_date and not end_date:
            print("\nNo dates provided. No changes made.")
            return

        if start_date and end_date:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            if start_dt > end_dt:
                print("\nError: Start date cannot be after end date.")
                return

        # Save dates
        set_project_dates(conn, user_id, project_name, start_date, end_date)

        print(f"\nDates updated for '{project_name}'.")
        if start_date:
            print(f"  Start: {start_date}")
        if end_date:
            print(f"  End: {end_date}")

    except ValueError:
        print("Invalid input. Please enter a number.")


def clear_specific_project_dates(conn, user_id):
    """Clear dates for a specific project."""
    # Get only projects with manual dates
    manual_dates_list = get_all_manual_dates(conn, user_id)

    if not manual_dates_list:
        print("\nNo projects with manual dates found.")
        return

    print(f"\n{'='*90}")
    print("Projects with Manual Dates:")
    print(f"{'='*90}")

    for idx, (project_name, start, end) in enumerate(manual_dates_list, start=1):
        print(f"  {idx}. {project_name} ({start or 'N/A'} to {end or 'N/A'})")

    print(f"{'='*90}")

    try:
        project_idx = int(input("\nEnter project number to clear: ").strip()) - 1

        if project_idx < 0 or project_idx >= len(manual_dates_list):
            print("Invalid project number.")
            return

        project_name = manual_dates_list[project_idx][0]

        confirm = input(f"\nClear manual dates for '{project_name}'? (y/n): ").strip().lower()

        if confirm in ['yes', 'y']:
            clear_project_dates(conn, user_id, project_name)
            print(f"\nManual dates cleared for '{project_name}'. Using automatic dates.")
        else:
            print("Cancelled.")

    except ValueError:
        print("Invalid input. Please enter a number.")


def reset_all_dates_to_auto(conn, user_id):
    """Clear all manual dates."""
    confirm = input("\nAre you sure you want to reset all dates to automatic? (y/n): ").strip().lower()

    if confirm in ['yes', 'y']:
        clear_all_project_dates(conn, user_id)
        print("\nAll manual dates cleared. Using automatic dates.")
    elif confirm in ['no', 'n']:
        print("Cancelled.")
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
