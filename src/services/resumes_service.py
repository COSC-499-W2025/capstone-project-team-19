from typing import List, Dict, Any
from src.db.resumes import list_resumes

def list_user_resumes(conn, user_id: int) -> List[Dict[str, Any]]:
    """
    Service method for listing resumes.
    """
    return list_resumes(conn, user_id)