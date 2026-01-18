from typing import List, Dict, Any
from src.db.skills import get_skill_events

def get_user_skills(conn, user_id: int) -> List[Dict[str, Any]]:
    rows = get_skill_events(conn, user_id)
    return [
        {
            "skill_name": row[0],
            "level": row[1],
            "score": row[2],
            "project_name": row[3],
            "actual_activity_date": row[4],
            "recorded_at": row[5]
        }
        for row in rows
    ]