import json
from typing import List, Dict, Any, Optional
from src.db.project_summaries import get_project_summaries_list, get_project_summary_by_id

def list_projects(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Service method for listing projects. DB access belongs here, not in routes.
    """
    return get_project_summaries_list(conn, user_id)

def get_project_by_id(conn,user_id: int, project_summary_id: int) -> Optional[Dict[str, Any]]:
    """
    Service method for retrieving a project by its ID.
    """
    row = get_project_summary_by_id(conn, user_id, project_summary_id)
    if not row:
        return None
     
    # Parse the summary_json
    try:
        summary_dict = json.loads(row["summary_json"])
    except json.JSONDecodeError:
        summary_dict = {}
    
    row_without_json = {k: v for k, v in row.items() if k != "summary_json"}
    
    # Flatten it
    return {
        **row_without_json, 
        **summary_dict  
    }