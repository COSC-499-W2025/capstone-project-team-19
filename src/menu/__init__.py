"""
src/menu/__init__.py

Menu module for user interface navigation.
"""

from .display import show_start_menu
from .project_summaries import view_old_project_summaries
from .resume import view_resume_items
from .portfolio import view_portfolio_items
from .delete import delete_old_insights
from .projects_list import project_list

__all__ = [
    "show_start_menu",
    "view_old_project_summaries",
    "view_resume_items",
    "view_portfolio_items",
    "delete_old_insights",
    "project_list",
]
