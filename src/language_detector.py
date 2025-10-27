import os

EXTENSION_TO_LANGUAGE = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".html": "HTML",
    ".css": "CSS",
    ".c": "C",
    ".cpp": "C++",
    ".h": "C/C++ Header"
}


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

    #look up languages based on extensions
    for row in results:
        ext = row[0]
        language = EXTENSION_TO_LANGUAGE.get(ext.lower())
        if language:
            languages.add(language)

    return list(languages)
    