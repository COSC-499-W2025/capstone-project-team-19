"""
Contains all required functions to check for duplicate ZIP files or projects in the database
"""

import os
from src.db import connect

def handle_existing_zip(conn, user_id, zip_path):
    cursor = conn.cursor()

    # There can only be one project connected to a single zip_path in the database (no duplicates)
    cursor.execute("""
        SELECT 1 FROM project_classifications
        WHERE user_id = ? AND zip_path = ?
        LIMIT 1;
    """, (user_id, zip_path))

    exists = cursor.fetchone() is not None
    if not exists:
        # no duplicates found, proceed to parsing
        return zip_path
    
    print(f"\nA zip from this path already exsist in the database.")
    print("Please choose one of the following options:\n")
    print("   [O]  Overwrite the old project")
    print("   [R]  Reuse the existing analysis (the uploaded file will be discarded)\n")
    choice = input("Your choice: ").strip().lower()

    if choice.startswith("o"):
        delete_existing_zip_data(conn, user_id, zip_path)
        print("Old data deleted. Re-uploading and re-parsing.")
        return zip_path
    
    elif choice.startswith("r"):
        print("Reusing existing analysis and skipping parsing.")
        return None
    
    else:
        print("Invalid choice. Skipping upload.")
        return None
    

def delete_existing_zip_data(conn, user_id, zip_path) -> None:
    """Deletes all database records for the given ZIP path"""

    cursor = conn.cursor()
    cursor.execute("""
        SELECT project_name FROM project_classifications
        WHERE user_id = ? AND zip_path = ?
    """, (user_id, zip_path))
    projects = [row[0] for row in cursor.fetchall()]

    for project_name in projects:
        cursor.execute("""
            DELETE FROM files
            WHERE user_id = ? AND project_name = ?
        """, (user_id, project_name))

    cursor.execute("""
        DELETE FROM project_classifications
        WHERE user_id = ? AND zip_path = ?
    """, (user_id, zip_path))

    conn.commit()
