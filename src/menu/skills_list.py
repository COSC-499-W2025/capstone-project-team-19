"""
src/menu/skills_list.py

Menu option for viewing chronological skills.
"""
from src.insights.chronological_skills import get_skill_timeline, print_skill_timeline

def view_chronological_skills(conn, user_id: int, username: str):
    """
    Display skills exercised in chronological order.
    """
    
    dated, undated = get_skill_timeline(conn, user_id)
    print_skill_timeline(dated, undated)

    return None