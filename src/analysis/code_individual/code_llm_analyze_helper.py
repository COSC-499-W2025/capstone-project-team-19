def _infer_project_root_folder(code_files, project_name: str | None, zip_name: str | None = None) -> str | None:
    wrappers = {"individual", "collaborative", "collab"}

    candidates = []
    for f in code_files:
        fp = (f.get("file_path") or "").replace("\\", "/").strip("/")
        if not fp:
            continue

        parts = fp.split("/")
        if len(parts) < 2:
            continue

        # Case: zip_name/<...>
        if zip_name and parts[0] == zip_name:
            if len(parts) < 3:
                continue

            second = parts[1].lower()
            # zip_name/individual/project_name/...
            if second in wrappers:
                if len(parts) >= 3:
                    candidates.append(parts[2])
            # zip_name/project_name/...
            else:
                candidates.append(parts[1])

        # Case: no zip_name prefix, fallback to first segment
        else:
            candidates.append(parts[0])

    if not candidates:
        return None

    # Prefer exact match if provided
    uniq = sorted(set(candidates))
    if project_name and project_name in uniq:
        return project_name

    from collections import Counter
    return Counter(candidates).most_common(1)[0][0]

def _normalize_language_token(lang: str) -> str:
    # "Python 97%" -> "python", "GoogleSQL 0%" -> "googlesql"
    return (lang or "").strip().split()[0].lower()

def _readme_mentions_detected_tech(
    readme_text: str | None,
    detected_languages: list[str] | None,
    detected_frameworks: list[str] | None,
) -> bool:
    """
    True iff README mentions ANY detected language/framework (evidence-based).
    Avoids manual keyword lists.
    """
    if not readme_text or not readme_text.strip():
        return False

    t = readme_text.lower()

    langs = [_normalize_language_token(x) for x in (detected_languages or []) if x]
    fws = [(x or "").strip().lower() for x in (detected_frameworks or []) if x]

    # remove empties / duplicates
    tech_terms = sorted(set([x for x in (langs + fws) if x]))

    return any(term in t for term in tech_terms)

