from .fingerprints import project_fingerprints
from .helpers import jaccard_similarity

from src.db import (
    find_existing_version_by_strict_fp,
    find_existing_version_by_loose_fp,
    get_latest_versions,
    get_project_key,
    get_hash_set_for_version,
    get_relpath_set_for_version,
    insert_project,
    insert_project_version,
    insert_version_files,
)

def register_project(conn, user_id: int, display_name: str, project_root: str, upload_id=None, high=0.85, low=0.35, noisy_file_count=10):
    fp_strict, fp_loose, entries = project_fingerprints(project_root)
    new_hashes = {h for _, h in entries}
    new_paths = {rel for rel, _ in entries}

    # 1. Check for exact duplicate: content + structure identical
    dupl_strict = find_existing_version_by_strict_fp(conn, user_id, fp_strict, exclude_upload_id=upload_id)
    if dupl_strict:
        project_key, version_key = dupl_strict
        return {"kind": "duplicate", "project_key": project_key, "version_key": version_key}

    # 1b. Project names are unique per user (projects.user_id + display_name).
    # If this name already exists, we must treat this upload as a new version of that project.
    existing_name_pk = get_project_key(conn, user_id, display_name)
    if existing_name_pk is not None:
        with conn:
            vk = insert_project_version(conn, int(existing_name_pk), upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {
            "kind": "new_version",
            "project_key": int(existing_name_pk),
            "version_key": vk,
            "forced_by_name": True,
        }

    # 2. Check for content-only match: same files, possibly different structure/names
    # This handles cases where files are renamed or restructured
    dupl_loose = find_existing_version_by_loose_fp(conn, user_id, fp_loose, exclude_upload_id=upload_id)
    if dupl_loose:
        project_key, version_key = dupl_loose
        # Content is identical but structure differs - ask user if it's a new version
        return {
            "kind": "ask",
            "best_match_project_key": project_key,
            "similarity": 1.0,
            "file_count": len(entries),
            # include data so caller can materialize a new project/version
            "upload_id": upload_id,
            "fingerprint_strict": fp_strict,
            "fingerprint_loose": fp_loose,
            "entries": entries,
        }

    # 3. Compare to existing projects (latest versions)
    latest = get_latest_versions(conn, user_id, exclude_upload_id=upload_id)

    # if user has no projects yet, create a new project snapshot
    if not latest:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_project", "project_key": pk, "version_key": vk}
    
    # Find best match by Jaccard similarity
    best_pk = None
    best_score = -1.0
    best_content_sim = -1.0
    best_path_sim = -1.0
    best_content_overlap = 0
    best_path_overlap = 0
    best_old_path_count = 0

    for pk, vk in latest.items():
        old_hashes = get_hash_set_for_version(conn, vk)
        old_paths = get_relpath_set_for_version(conn, vk)

        content_sim = jaccard_similarity(new_hashes, old_hashes)
        path_sim = jaccard_similarity(new_paths, old_paths)
        content_overlap = len(new_hashes & old_hashes)
        path_overlap = len(new_paths & old_paths)

        # Combined scoring:
        # - Hash overlap is great for large projects
        # - Path/structure overlap matters a lot for small projects where hash-only Jaccard is very brittle
        score = (0.7 * path_sim) + (0.3 * content_sim)

        if score > best_score:
            best_score = score
            best_content_sim = content_sim
            best_path_sim = path_sim
            best_content_overlap = content_overlap
            best_path_overlap = path_overlap
            best_old_path_count = len(old_paths)
            best_pk = pk

    # Safety: if for some reason we couldn't compare, treat as new project
    if best_pk is None:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {"kind": "new_project", "project_key": pk, "version_key": vk}

    # Scenario 2: new version of best match
    if best_content_sim >= high:
        with conn:
            vk = insert_project_version(conn, best_pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {
            "kind": "new_version",
            "project_key": best_pk,
            "version_key": vk,
            "similarity": best_content_sim,
            "path_similarity": best_path_sim,
        }

    # Small projects are noisy: hash-only Jaccard treats any change as "totally different".
    # Prefer prompting rather than forcing "new project" when we have *any* reasonable signal that this might be a related version.
    if len(entries) < noisy_file_count:
        min_file_count = min(len(entries), best_old_path_count) if best_old_path_count else len(entries)
        path_overlap_threshold = 1 if min_file_count <= 4 else 2

        should_ask = (
            # Strong structure match (even if content changed)
            best_path_sim >= 0.9
            # Some structure overlap after a restructure/rename
            or best_path_overlap >= path_overlap_threshold
            # Some unchanged files (works even if paths moved, because hashes match)
            or best_content_overlap >= 2
            # Weak fallback: overall relatedness
            or best_score >= 0.45
        )

        if should_ask:
            return {
                "kind": "ask",
                "best_match_project_key": best_pk,
                "similarity": best_content_sim,
                "path_similarity": best_path_sim,
                "file_count": len(entries),
                "path_overlap": best_path_overlap,
                "content_overlap": best_content_overlap,
                # include data so caller can materialize a new project/version
                "upload_id": upload_id,
                "fingerprint_strict": fp_strict,
                "fingerprint_loose": fp_loose,
                "entries": entries,
            }

    # Scenario 3: new project
    if best_content_sim <= low:
        with conn:
            pk = insert_project(conn, user_id, display_name)
            vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
            insert_version_files(conn, vk, entries)
        return {
            "kind": "new_project",
            "project_key": pk,
            "version_key": vk,
            "similarity": best_content_sim,
            "path_similarity": best_path_sim,
        }

    # Middle band = ask user
    return {
        "kind": "ask",
        "best_match_project_key": best_pk,
        "similarity": best_content_sim,
        "path_similarity": best_path_sim,
        # include data so caller can materialize a new project/version
        "upload_id": upload_id,
        "fingerprint_strict": fp_strict,
        "fingerprint_loose": fp_loose,
        "entries": entries,
    }