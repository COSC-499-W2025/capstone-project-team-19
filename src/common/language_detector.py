from src.common.extension_catalog import get_languages_for_extension


def detect_languages(conn, project_name):
    """Detects all programming languages used in the given project folder."""
 
    cursor = conn.cursor()
    #Get all code file extensions in the project 
    query = """
        SELECT extension
        FROM files
        WHERE project_name = ? AND file_type = 'code'
    """
    cursor.execute(query, (project_name,))
    results = cursor.fetchall()

    languages = set()

    # look up languages based on extensions (case-insensitive)
    for row in results:
        ext = row[0] or ""
        languages.update(get_languages_for_extension(ext))

    return sorted(languages)
    
