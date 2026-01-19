from .fingerprints import project_fingerprints
from .helpers import jaccard_similarity

from src.db import find_existing_version_by_strict_fp, find_existing_version_by_loose_fp, get_latest_versions, get_hash_set_for_version, insert_project, insert_project_version, insert_version_files

def register_project(conn, user_id: int, display_name: str, project_root: str, upload_id=None, high=0.85, low=0.35, noisy_file_count=10):
    fp_strict, fp_loose, entries = project_fingerprints(project_root)
    new_hashes = {h for _, h in entries}

    # 1. Check for exact duplicate: content + structure identical
    dupl_strict = find_existing_version_by_strict_fp(conn, user_id, fp_strict)
    if dupl_strict:
        project_key, version_key = dupl_strict
        return {"kind": "duplicate", "project_key": project_key, "version_key": version_key}

    # 2. Check for content-only match: same files, possibly different structure/names
    # This handles cases where files are renamed or restructured
    dupl_loose = find_existing_version_by_loose_fp(conn, user_id, fp_loose)
    if dupl_loose:
        project_key, version_key = dupl_loose
        # Content is identical but structure differs - ask user if it's a new version
        return {"kind": "ask", "best_match_project_key": project_key, "similarity": 1.0, "file_count": len(entries)}

    # 3. Compare to existing projects (latest versions)
    latest = get_latest_versions(conn, user_id)

    # if user has no projects yet, create a new project snapshot
    if not latest:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_project", "project_key": pk, "version_key": vk}
    
    # Find best match by Jaccard similarity
    best_pk = None
    best_sim = -1.0

    for pk, vk in latest.items():
        old_hashes = get_hash_set_for_version(conn, vk)
        sim = jaccard_similarity(new_hashes, old_hashes)
        if sim > best_sim:
            best_sim = sim
            best_pk = pk

    # Safety: if for some reason we couldn't compare, treat as new project
    if best_pk is None:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_project", "project_key": pk, "version_key": vk}

    # Scenario 2: new version of best match
    if best_sim >= high:
        with conn:
            vk = insert_project_version(conn, best_pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_version", "project_key": best_pk, "version_key": vk, "similarity": best_sim}

    # Small projects are noisy so default to new project unless clearly a version
    if len(entries) < noisy_file_count:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_project", "project_key": pk, "version_key": vk, "similarity": best_sim, "file_count": len(entries)}

    # Scenario 3: new project
    if best_sim <= low:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_project", "project_key": pk, "version_key": vk, "similarity": best_sim}

    # Middle band = ask user
    return {"kind": "ask", "best_match_project_key": best_pk, "similarity": best_sim}