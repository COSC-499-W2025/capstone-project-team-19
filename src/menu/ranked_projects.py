"""
src/menu/ranked_projects.py

Display ranked projects with their scores.
"""

from src.insights.rank_projects.rank_project_importance import collect_project_data


def view_ranked_projects(conn, user_id: int, username: str) -> None:
    """
    Display all projects ranked by their importance scores.
    
    Args:
        conn: Database connection
        user_id: User ID
        username: Username for display
    """
    
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

