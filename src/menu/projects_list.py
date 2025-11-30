"""
src/menu/project_list.py

Menu option for viewing a list of all projects in chronological order.
"""
from src.db import get_all_projects_with_dates
from datetime import datetime

def project_list(conn, user_id: int, username: str):
    """
    Display all projects in chronological order by completion date (newest first).
    """
    print("\n" + "="*60)
    print("ALL PROJECTS (CHRONOLOGICAL LIST)")
    print("="*60)

    # Get all projects with actual completion dates
    projects = get_all_projects_with_dates(conn, user_id)

    if not projects:
        print(f"\nNo projects found for {username}.")
        print("You haven't analyzed any projects yet.")
        input("\nPress Enter to return to main menu...")
        return None

    # Display list of projects
    print(f"\n{username}'s Projects (Newest First):\n")
    for project in projects:
        project_name = project['project_name']
        date_str = project['actual_project_date']
        
        # Format date if available
        if date_str:
            try:
                # Try parsing ISO format date
                if 'T' in date_str:
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Try other common formats
                    dt = datetime.strptime(date_str.split()[0], '%Y-%m-%d')
                formatted_date = dt.strftime('%b %d %Y')
            except (ValueError, AttributeError):
                formatted_date = date_str
        else:
            formatted_date = 'Date unknown'
        
        # Format with right-aligned date (using 60 char width to match header)
        print(f"- {project_name:<45} [{formatted_date}]")

    input("\nPress Enter to return to main menu...")
    return None
