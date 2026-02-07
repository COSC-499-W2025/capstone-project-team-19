"""
Contains all required functions to check for duplicate ZIP files or projects in the database
"""

import os
from src.db import connect

def handle_existing_zip(conn, user_id, zip_path):
    cursor = conn.cursor()

    # There can only be one upload connected to a single zip_path in the database (no duplicates)
    cursor.execute("""
        SELECT 1 FROM uploads
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
    upload_ids = [
        row[0]
        for row in cursor.execute(
            """
            SELECT upload_id
            FROM uploads
            WHERE user_id = ? AND zip_path = ?
            """,
            (user_id, zip_path),
        ).fetchall()
    ]

    if not upload_ids:
        return

    # Find impacted projects (by project_key) and their display names.
    impacted = cursor.execute(
        f"""
        SELECT DISTINCT p.project_key, p.display_name
        FROM project_versions pv
        JOIN projects p ON p.project_key = pv.project_key
        WHERE p.user_id = ?
          AND pv.upload_id IN ({",".join(["?"] * len(upload_ids))})
        """,
        (user_id, *upload_ids),
    ).fetchall()

    # Delete versions for those uploads (cascades into version_files + version_key-keyed metrics).
    cursor.execute(
        f"DELETE FROM project_versions WHERE upload_id IN ({','.join(['?'] * len(upload_ids))})",
        tuple(upload_ids),
    )

    # Delete file rows for impacted project display names; config_files by project_key.
    for project_key, display_name in impacted:
        cursor.execute(
            "DELETE FROM files WHERE user_id = ? AND project_name = ?",
            (user_id, display_name),
        )
        cursor.execute(
            "DELETE FROM config_files WHERE user_id = ? AND project_key = ?",
            (user_id, project_key),
        )

    # Remove project rows that now have zero versions.
    for project_key, _display_name in impacted:
        still_has_versions = cursor.execute(
            "SELECT 1 FROM project_versions WHERE project_key = ? LIMIT 1",
            (project_key,),
        ).fetchone()
        if not still_has_versions:
            cursor.execute("DELETE FROM projects WHERE project_key = ?", (project_key,))

    # Finally delete the uploads row(s).
    cursor.execute(
        f"DELETE FROM uploads WHERE upload_id IN ({','.join(['?'] * len(upload_ids))})",
        tuple(upload_ids),
    )

    conn.commit()
