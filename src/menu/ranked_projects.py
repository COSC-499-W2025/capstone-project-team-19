"""
src/menu/ranked_projects.py

Display ranked projects with their scores.
"""

import json
from src.insights.rank_projects.rank_project_importance import collect_project_data
from src.db import get_project_summary_by_name


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
        print("3. Return to main menu")

        choice = input("\nPlease select an option (1-3): ").strip()
        
        if choice == "1":
            view_all_ranked_projects(conn, user_id, username)
        elif choice == "2":
            view_top_projects_summaries(conn, user_id, username)
        elif choice == "3":
            return None
        else:
            print("Invalid choice. Please enter a number between 1 and 3.")


def view_all_ranked_projects(conn, user_id, username) -> None:
    try:
        project_scores = collect_project_data(conn, user_id)
        
        if not project_scores:
            print(f"\n{'='*80}")
            print("No projects found. Please analyze some projects first.")
            print(f"{'='*80}\n")
            return

        print(f"\n{'='*80}\n")
        print(f"Ranked Projects for {username}")
        print(f"\n{'='*80}\n")
        print(f"Found {len(project_scores)} project(s):\n")
        print(f"{'Rank':<6} {'Project Name':<50} {'Score':<10}")
        print("-" * 80)
        
        for rank, (project_name, score) in enumerate(project_scores, start=1):
            # Truncate long project names
            display_name = project_name[:47] + "..." if len(project_name) > 50 else project_name
            print(f"{rank:<6} {display_name:<50} {score:.3f}")
        
        print(f"\n{'='*80}\n")
        
    except Exception as e:
        print(f"Error ranking projects: {e}")
        print(f"{'='*80}\n")


def view_top_projects_summaries(conn, user_id, username) -> None:
    try:
        project_scores = collect_project_data(conn, user_id)
        project_scores.sort(key=lambda x: x[1], reverse=True)

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
            print(f"\n{'='*80}")
            print(f"Rank #{rank}: {project_name} (Score: {score:.3f})")
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
