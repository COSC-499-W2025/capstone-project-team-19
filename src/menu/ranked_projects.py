"""
src/menu/ranked_projects.py

Display ranked projects with their scores.
"""

import json
from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import (
    get_project_summary_by_name,
    get_all_project_ranks,
    set_project_rank,
    clear_project_rank,
    clear_all_rankings,
    bulk_set_rankings
)


def view_ranked_projects(conn, user_id: int, username: str) -> None:
    """
    Display all projects ranked by their importance scores.

    Args:
        conn: Database connection
        user_id: User ID
        username: Username for display
    """

    while True:
        print()
        print("1. View all ranked projects")
        print("2. View summaries of top projects")
        print("3. Manually reorder projects")
        print("4. Set specific project rank")
        print("5. Reset to automatic ranking")
        print("6. Return to main menu")

        choice = input("\nPlease select an option (1-6): ").strip()

        if choice == "1":
            view_all_ranked_projects(conn, user_id, username)
        elif choice == "2":
            view_top_projects_summaries(conn, user_id, username)
        elif choice == "3":
            interactive_reorder(conn, user_id)
        elif choice == "4":
            set_specific_rank(conn, user_id)
        elif choice == "5":
            reset_to_auto_ranking(conn, user_id)
        elif choice == "6":
            return None
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")


def view_all_ranked_projects(conn, user_id, username) -> None:
    try:
        project_scores = collect_project_data(conn, user_id)
        # Get manual rankings to show indicators
        manual_ranks = dict(get_all_project_ranks(conn, user_id))
        if not project_scores:
            print(f"\n{'='*80}")
            print("No projects found. Please analyze some projects first.")
            print(f"{'='*80}\n")
            return

        print(f"\n{'='*80}\n")
        print(f"Ranked Projects for {username}")
        print(f"\n{'='*80}\n")
        print(f"Found {len(project_scores)} project(s):\n")
        print(f"{'Rank':<6} {'Project Name':<50} {'Score':<10} {'Type':<8}")
        print("-" * 80)

        for rank, (project_name, score) in enumerate(project_scores, start=1):
            # Truncate long project names
            display_name = project_name[:47] + "..." if len(project_name) > 50 else project_name

            # Check if manually ranked
            rank_type = "MANUAL" if project_name in manual_ranks and manual_ranks[project_name] is not None else "AUTO"

            print(f"{rank:<6} {display_name:<50} {score:.3f}    {rank_type:<8}")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"Error ranking projects: {e}")
        print(f"{'='*80}\n")


def view_top_projects_summaries(conn, user_id, username) -> None:
    try:
        # collect_project_data already returns projects sorted with manual rankings respected
        project_scores = collect_project_data(conn, user_id)

        # Get manual rankings to show indicators
        manual_ranks = dict(get_all_project_ranks(conn, user_id))

        top_n = 3
        top_projects = project_scores[:top_n]

        if not top_projects:
            print(f"\n{'='*80}")
            print("No projects found. Please analyze some projects first.")
            print(f"{'='*80}\n")
            return

        print(f"\n{'='*80}\n")
        print(f"Top {len(top_projects)} Projects for {username}")
        print(f"\n{'='*80}\n")

        for rank, (project_name, score) in enumerate(top_projects, start=1):
            # Check if manually ranked
            rank_type = " [MANUAL]" if project_name in manual_ranks and manual_ranks[project_name] is not None else ""

            print(f"\n{'='*80}")
            print(f"Rank #{rank}: {project_name} (Score: {score:.3f}){rank_type}")
            print(f"{'='*80}")
            
            # Get project summary
            summary_data = get_project_summary_by_name(conn, user_id, project_name)
            
            if summary_data:
                try:
                    summary_dict = json.loads(summary_data['summary_json'])
                    
                    # Display project type and mode
                    print(f"\nProject Type: {summary_data['project_type'] or 'N/A'}")
                    print(f"Project Mode: {summary_data['project_mode'] or 'N/A'}")
                    
                    # Display summary text if available
                    if 'summary_text' in summary_dict and summary_dict['summary_text']:
                        print(f"\n{'-'*80}")
                        print("SUMMARY:")
                        print(f"{'-'*80}")
                        print(summary_dict['summary_text'])
                    else:
                        print("\nNo summary text available for this project.")
                        
                except json.JSONDecodeError:
                    print("\nError: Could not parse project summary JSON.")
            else:
                print(f"\nError: Could not find summary for project '{project_name}'.")
            
            print()  # Add spacing between projects
        
        print(f"{'='*80}\n")
            
    except Exception as e:
        print(f"Error printing top projects summaries: {e}")
        print(f"{'='*80}\n")

def interactive_reorder(conn, user_id):
    projects = collect_project_data(conn, user_id, respect_manual_ranking=False)

    if not projects:
        print("\nNo projects found.")
        return

    print(f"\n{'='*80}")
    print("Interactive Project Reordering")
    print(f"{'='*80}")
    print("Current order (by auto-score):")

    for rank, (project_name, score) in enumerate(projects, start=1):
        print(f"  {rank}. {project_name} (score: {score:.3f})")

    print(f"\n{'='*80}")
    print("Enter new order as comma-separated project names (or 'cancel'):")
    print("Example: project3, project1, project2")
    print(f"{'='*80}")

    user_input = input("\nNew order: ").strip()

    if user_input.lower() == 'cancel':
        print("Cancelled.")
        return

    # Parse input
    new_order = [name.strip() for name in user_input.split(',')]
    project_names = {name for name, _ in projects}

    # Validate
    if not all(name in project_names for name in new_order):
        print("\nError: Some project names are invalid. Please try again.")
        return

    # Apply new rankings
    rankings = [(name, rank) for rank, name in enumerate(new_order, start=1)]
    bulk_set_rankings(conn, user_id, rankings)

    print(f"\nSuccessfully reordered {len(rankings)} projects!")
    print("Note: Projects not in your list will retain auto-ranking.")


def set_specific_rank(conn, user_id):
    """Set rank for a specific project."""
    projects = collect_project_data(conn, user_id, respect_manual_ranking=False)

    if not projects:
        print("\nNo projects found.")
        return

    print(f"\n{'='*80}")
    print("Available Projects:")
    print(f"{'='*80}")

    for idx, (project_name, score) in enumerate(projects, start=1):
        print(f"  {idx}. {project_name} (auto-score: {score:.3f})")

    print(f"{'='*80}")

    try:
        project_idx = int(input("\nEnter project number: ").strip()) - 1

        if project_idx < 0 or project_idx >= len(projects):
            print("Invalid project number.")
            return

        project_name = projects[project_idx][0]

        rank_input = input(f"Enter rank for '{project_name}' (or 'auto' for automatic): ").strip()

        if rank_input.lower() == 'auto':
            clear_project_rank(conn, user_id, project_name)
            print(f"\n'{project_name}' now uses automatic ranking.")
        else:
            rank = int(rank_input)
            if rank < 1:
                print("Rank must be 1 or higher.")
                return

            set_project_rank(conn, user_id, project_name, rank)
            print(f"\n'{project_name}' set to rank #{rank}.")

    except ValueError:
        print("Invalid input. Please enter a number.")


def reset_to_auto_ranking(conn, user_id):
    """Clear all manual rankings."""
    confirm = input("\nAre you sure you want to reset all rankings to automatic? (y/n): ").strip().lower()

    if confirm == 'yes' or confirm == 'y':
        clear_all_rankings(conn, user_id)
        print("\n All manual rankings cleared. Using automatic ranking.")
    elif confirm == 'no' or confirm == 'n':
        print("Cancelled.")
    else:
        print("Invalid input. Please enter 'yes' or 'no'.")
