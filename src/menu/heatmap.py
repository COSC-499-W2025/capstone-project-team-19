import textwrap
from typing import List, Dict, Any, Optional

def view_activity_heatmap(conn, user_id: int):
    """
    Display a heatmap of user activity by date.
    Shows number of projects created per day.
    """
    rows = conn.execute(
        """
        SELECT DATE(created_at) AS activity_date, COUNT(*) AS project_count
        FROM projects
        WHERE user_id = ?
        GROUP BY DATE(created_at)