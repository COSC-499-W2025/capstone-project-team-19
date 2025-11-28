import json
from src.db import get_project_summaries_list, get_project_summary_by_name


def view_old_project_summaries(conn, user_id: int, username: str):
    """
    Display previously analyzed project summaries.
    """
    while True:
        print("\n" + "="*60)
        print("VIEW OLD PROJECT SUMMARIES")
        print("="*60)

        # Get all project summaries for this user
        summaries = get_project_summaries_list(conn, user_id)

        if not summaries:
            print(f"\nNo project summaries found for {username}.")
            print("You haven't analyzed any projects yet.")
            input("\nPress Enter to return to main menu...")
            return None

        # Display list of projects
        print(f"\n{username}'s Projects List:\n")
        for idx, summary in enumerate(summaries, start=1):
            project_type = summary['project_type'] or 'unknown'
            project_mode = summary['project_mode'] or 'unknown'
            created_at = summary['created_at']
            print(f"{idx}. {summary['project_name']} ({project_mode} {project_type} Project, Analyzed: {created_at})")

        if len(summaries) == 1:
            display_project_summary(conn, user_id, summaries[0]['project_name'])
            input("\nPress Enter to return to main menu...")
            return None

        print("\n" + "-"*60)
        choice = input(f"\nEnter the number (1-{len(summaries)}) to view details, or 'q' to quit: ").strip().lower()

        if choice == 'q':
            print("\nReturning to main menu...")
            return None

        try:
            idx = int(choice)
            if 1 <= idx <= len(summaries):
                selected_project = summaries[idx - 1]
                display_project_summary(conn, user_id, selected_project['project_name'])

                # Ask if user wants to view another project
                print("\n" + "-"*60)
                continue_choice = input("\nView another project? (y/n): ").strip().lower()
                if continue_choice not in {'y', 'yes'}:
                    print("\nReturning to main menu...")
                    return None
            else:
                print(f"Please enter a number between 1 and {len(summaries)}.")
        except ValueError:
            print("Invalid input. Please enter a number or 'q' to quit.")


def display_project_summary(conn, user_id: int, project_name: str):
    """
    Display detailed summary for a specific project.
    """
    summary_data = get_project_summary_by_name(conn, user_id, project_name)

    if not summary_data:
        print(f"\nError: Could not find summary for project '{project_name}'.")
        return

    print("\n" + "="*60)
    print(f"PROJECT SUMMARY: {project_name}")
    print("="*60)

    # Parse the JSON summary
    try:
        summary_dict = json.loads(summary_data['summary_json'])

        # Display basic info
        print(f"\nProject Type: {summary_data['project_type'] or 'N/A'}")
        print(f"Project Mode: {summary_data['project_mode'] or 'N/A'}")
        print(f"Analyzed At: {summary_data['created_at']}")

        # Display summary text if available
        if 'summary_text' in summary_dict and summary_dict['summary_text']:
            print("\n" + "-"*60)
            print("SUMMARY:")
            print("-"*60)
            print(summary_dict['summary_text'])

    except json.JSONDecodeError:
        print("\nError: Could not parse project summary JSON.")
        print("Raw data:")
        print(summary_data['summary_json'][:500])  # Show first 500 chars
