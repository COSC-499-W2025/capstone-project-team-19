"""
src/menu/__init__.py

Menu module for user interface navigation.
"""

from .display import show_start_menu
from .project_summaries import view_old_project_summaries
from .resume import view_resume_items
from .portfolio import view_portfolio_items
from .feedback import view_project_feedback
from .delete import delete_old_insights
from .projects_list import project_list
from .skills_list import view_chronological_skills
from .ranked_projects import view_ranked_projects
from .project_dates import edit_project_dates_menu
from .delete import delete_old_insights
from .thumbnails import manage_project_thumbnails

__all__ = [
    "show_start_menu",
    "view_old_project_summaries",
    "view_resume_items",
    "view_portfolio_items",
    "view_project_feedback",
    "delete_old_insights",
    "project_list",
    "view_chronological_skills",
    "view_ranked_projects",
    "edit_project_dates_menu",
    "delete_old_insights",
    "manage_project_thumbnails",
]
