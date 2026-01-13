from typing import List, Dict, Any
from src.db.project_summaries import get_project_summaries_list

def list_projects(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Service method for listing projects. DB access belongs here, not in routes.
    """
    return get_project_summaries_list(conn, user_id)
