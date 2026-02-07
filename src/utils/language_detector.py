from src.utils.extension_catalog import get_languages_for_extension


def detect_languages(conn, user_id: int, project_name: str, version_key: int | None = None):
    """Detects all programming languages used in the given project folder."""
    from src.db.files import get_code_extensions_for_project, get_code_extensions_for_version
    if version_key is not None:
        exts = get_code_extensions_for_version(conn, user_id, version_key)
    else:
        exts = get_code_extensions_for_project(conn, user_id, project_name)
    results = [(e,) for e in exts]

    languages = set()

    # look up languages based on extensions (case-insensitive)
    for row in results:
        ext = row[0] or ""
        languages.update(get_languages_for_extension(ext))

    return sorted(languages)
    
