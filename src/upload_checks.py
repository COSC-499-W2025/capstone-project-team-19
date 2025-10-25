"""
Contains all required functions to check for duplicate ZIP files or projects in the database
"""

import os
from db import connect

def check_existing_zip(conn, user_id, zip_path):
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
    
    print(f"\nA zip from this path already exsist in the database. Please choose one of the following:")
    print(f"O --> Overwite the old project")
    print(f"\nD --> Duplicate the project (the zip_path will be modified to be unique)")
    print(f"\nR --> Reuse the existing analysis (the uploaded file will be discarded)")
    choice = input("").strip().lower()

    if choice.startswith("o"):
        delete_existing_zip_data(conn, user_id, zip_path)
        print("Old data deleted. Re-uploading and re-parsing.")
        return zip_path
    
    elif choice.startswith("d"):
        new_path = generate_duplicate_zip_name(conn, user_id, zip_path)
        print(f"Creating a duplicate entry as: {new_path}")
        return new_path
    
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
        """, (user_id, zip_path))

    cursor.execute("""
        DELETE FROM project_classifications
        WHERE user_id = ? AND zip_path = ?
    """, (user_id, zip_path))

    conn.commit()

def generate_duplicate_zip_name(conn, user_id, zip_path) -> str:
    """Generates a new unique ZIP path by appending an incrementing number"""
    base, ext = os.path.splitext(zip_path)
    counter = 1
    new_path = f"{base}_{counter}{ext}"

    while _zip_exists(conn, user_id, new_path):
        counter += 1
        new_path = f"{base}_{counter}{ext}"
    
    return new_path

def _zip_exists(conn, user_id, zip_path) -> bool:
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 1 FROM project_classifications
        WHERE user_id = ? AND zip_path = ?
        LIMIT 1;
    """, (user_id, zip_path))

    return cursor.fetchone() is not None