import os
import sqlite3
from src.utils.deduplication.register_project import register_project
from src.db.deduplication import insert_project, insert_project_version, insert_version_files
from src import constants

def handle_dedup_result(conn, user_id, result, display_name):
    """Handle register_project result, prompting user when needed. Returns final display_name or None to skip."""
    kind = result["kind"]
    
    if kind == "duplicate":
        pk = result["project_key"]
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else "unknown"
        print(f"\nProject '{display_name}' is an exact duplicate of '{existing}'. Skipping upload.")
        return None
    
    elif kind == "ask":
        pk = result["best_match_project_key"]
        sim = result["similarity"]
        path_sim = result.get("path_similarity")
        file_count = result.get("file_count", "unknown")
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else "unknown"
        extra = ""
        if path_sim is not None:
            extra += f", path similarity: {path_sim:.1%}"
        if file_count != "unknown":
            extra += f", files: {file_count}"
        print(f"\nProject '{display_name}' looks related to '{existing}' (similarity: {sim:.1%}{extra}).")
        print("Is this:")
        print("  [N]  New project")
        print("  [V]  New version of the existing project")
        choice = input("Choice: ").strip().lower()
        if choice.startswith("v"):
            return existing
        return display_name
    
    elif kind == "new_version":
        pk = result["project_key"]
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else display_name
        print(f"Project '{display_name}' detected as new version of '{existing}'.")
        return existing
    
    return display_name


def handle_dedup_result_with_version(conn, user_id, result, display_name):
    """
    Like handle_dedup_result(), but returns structured output including version_key.
    For 'ask' results, this will materialize either a new project or new version
    using the fingerprints + entries included in the register_project() output.
    """
    kind = result["kind"]

    if kind == "duplicate":
        pk = result["project_key"]
        vk = result.get("version_key")
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else "unknown"
        print(f"\nProject '{display_name}' is an exact duplicate of '{existing}'. Skipping upload.")
        return {"action": "skip", "final_name": None, "project_key": pk, "version_key": vk, "kind": kind}

    if kind == "new_version":
        pk = result["project_key"]
        vk = result.get("version_key")
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else display_name
        print(f"Project '{display_name}' detected as new version of '{existing}'.")
        return {"action": "keep", "final_name": existing, "project_key": pk, "version_key": vk, "kind": kind}

    if kind == "new_project":
        pk = result.get("project_key")
        vk = result.get("version_key")
        return {"action": "keep", "final_name": display_name, "project_key": pk, "version_key": vk, "kind": kind}

    if kind == "ask":
        pk = result["best_match_project_key"]
        sim = result["similarity"]
        path_sim = result.get("path_similarity")
        file_count = result.get("file_count", "unknown")
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else "unknown"
        extra = ""
        if path_sim is not None:
            extra += f", path similarity: {path_sim:.1%}"
        if file_count != "unknown":
            extra += f", files: {file_count}"
        print(f"\nProject '{display_name}' looks related to '{existing}' (similarity: {sim:.1%}{extra}).")
        print("Is this:")
        print("  [N]  New project")
        print("  [V]  New version of the existing project")
        choice = input("Choice: ").strip().lower()

        fp_strict = result.get("fingerprint_strict")
        fp_loose = result.get("fingerprint_loose")
        entries = result.get("entries") or []
        upload_id = result.get("upload_id")

        if choice.startswith("v"):
            vk = result.get("version_key")
            if vk is None and fp_strict and entries:
                with conn:
                    vk = insert_project_version(conn, pk, upload_id, fp_strict, fp_loose)
                    insert_version_files(conn, vk, entries)
            return {"action": "keep", "final_name": existing, "project_key": pk, "version_key": vk, "kind": "ask->new_version"}

        # default: new project
        new_pk = result.get("project_key")
        new_vk = result.get("version_key")
        if (new_pk is None or new_vk is None) and fp_strict and entries:
            with conn:
                new_pk = insert_project(conn, user_id, display_name)
                new_vk = insert_project_version(conn, new_pk, upload_id, fp_strict, fp_loose)
                insert_version_files(conn, new_vk, entries)
        return {"action": "keep", "final_name": display_name, "project_key": new_pk, "version_key": new_vk, "kind": "ask->new_project"}

    # fallback
    return {"action": "keep", "final_name": display_name, "project_key": None, "version_key": None, "kind": kind}

def run_deduplication_for_projects(conn, user_id, target_dir, layout):
    """Run deduplication for all projects in layout. Returns set of project names to skip."""
    root_name = layout.get("root_name")
    all_projects = set(layout.get("auto_assignments", {}).keys())
    all_projects.update(layout.get("pending_projects", []))
    
    if not all_projects:
        return set()
    
    if root_name:
        base_path = os.path.join(target_dir, root_name)
    else:
        base_path = target_dir
    
    skipped = set()
    
    for project_name in all_projects:
        # Try to find project directory, check common patterns including individual/collaborative subfolders
        candidates = [
            os.path.join(base_path, project_name),
            os.path.join(target_dir, project_name),
        ]
        if root_name:
            # Also check if project is directly under root, or in individual/collaborative subfolders
            candidates.insert(0, os.path.join(target_dir, root_name, project_name))
            candidates.insert(0, os.path.join(target_dir, root_name, "individual", project_name))
            candidates.insert(0, os.path.join(target_dir, root_name, "collaborative", project_name))
        
        project_dir = None
        for cand in candidates:
            if os.path.isdir(cand):
                project_dir = cand
                break
        
        if not project_dir: continue  # Skip if can't find directory
        
        try:
            result = register_project(conn, user_id, project_name, project_dir)
            final_name = handle_dedup_result(conn, user_id, result, project_name)
            if final_name is None:
                skipped.add(project_name)
        except Exception as e:
            if constants.VERBOSE:
                print(f"Warning: Deduplication failed for {project_name}: {e}")
            continue
    
    return skipped


def run_deduplication_for_projects_detailed(conn, user_id, target_dir, layout):
    """
    Run deduplication for all projects in layout.
    Returns (skipped_projects, decisions_by_original_project_name).
    decisions include final_name + version_key when available.
    """
    root_name = layout.get("root_name")
    all_projects = set(layout.get("auto_assignments", {}).keys())
    all_projects.update(layout.get("pending_projects", []))

    if not all_projects:
        return set(), {}

    if root_name:
        base_path = os.path.join(target_dir, root_name)
    else:
        base_path = target_dir

    skipped: set[str] = set()
    decisions: dict[str, dict] = {}

    for project_name in all_projects:
        candidates = [
            os.path.join(base_path, project_name),
            os.path.join(target_dir, project_name),
        ]
        if root_name:
            candidates.insert(0, os.path.join(target_dir, root_name, project_name))
            candidates.insert(0, os.path.join(target_dir, root_name, "individual", project_name))
            candidates.insert(0, os.path.join(target_dir, root_name, "collaborative", project_name))

        project_dir = None
        for cand in candidates:
            if os.path.isdir(cand):
                project_dir = cand
                break
        if not project_dir:
            continue

        try:
            result = register_project(conn, user_id, project_name, project_dir)
            decision = handle_dedup_result_with_version(conn, user_id, result, project_name)
            if decision.get("action") == "skip":
                skipped.add(project_name)
            else:
                decisions[project_name] = decision
        except Exception as e:
            if constants.VERBOSE:
                print(f"Warning: Deduplication failed for {project_name}: {e}")
            continue

    return skipped, decisions
