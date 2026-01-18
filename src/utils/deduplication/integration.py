import os
import sqlite3
from src.utils.deduplication.register_project import register_project
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
        file_count = result.get("file_count", "unknown")
        row = conn.execute("SELECT display_name FROM projects WHERE project_key = ?", (pk,)).fetchone()
        existing = row[0] if row else "unknown"
        print(f"\nProject '{display_name}' looks related to '{existing}' (similarity: {sim:.1%}" + 
              (f", files: {file_count}" if file_count != "unknown" else "") + ").")
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
        # Try to find project directory, check common patterns
        candidates = [
            os.path.join(base_path, project_name),
            os.path.join(target_dir, project_name),
        ]
        if root_name:
            # Also check if project is directly under root
            candidates.insert(0, os.path.join(target_dir, root_name, project_name))
        
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
