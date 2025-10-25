"""
Contains all required functions to check for duplicate ZIP files or projects in the database
"""

import os
from db import connect

def check_existing_zip(conn, user_id, zip_path):
    zip_name = os.path.basename(zip_path) # get the zip name

    cursor = conn.cursor()

    # There can only be one project connected to a single zip_path in the database (no duplicates)
    cursor.execute("""
        SELECT 1 FROM project_classifications
        WHERE user_id = ? AND zip_name = ?
        LIMIT 1;
    """, (user_id, zip_name))

    return cursor.fetchone() is not None