import json
import os
from typing import Dict, List

from src.analysis.skills.utils.skill_levels import score_to_level
from src.analysis.skills.detectors.code.detector_registry import CODE_DETECTOR_FUNCTIONS
from src.analysis.skills.buckets.code_buckets import CODE_SKILL_BUCKETS
from src.db import insert_project_skill
from src.utils.helpers import read_file_content


def extract_code_skills(conn, user_id, project_name, classification, files):
    """
    Main entry point for extracting code-related skills from a project.
    Steps:
        1. Get zip_name for path construction
        2. Load file contents from disk
        3. Run detectors
        4. Aggregate results into skill buckets
        5. Compute skill scores + levels
        6. Save results in the DB
    """

    print(f"\n[SKILL EXTRACTION] Running CODE skill extraction for {project_name}")

    # Get zip_name to construct correct file paths
    zip_name = _get_zip_name(conn, user_id, project_name)
    if not zip_name:
        print(f"[SKILL EXTRACTION] Warning: Could not determine zip_name for {project_name}, skipping")
        return

    # Load file contents before running detectors
    files_with_content = _load_file_contents(files, zip_name)

    detector_results = run_all_code_detectors(files_with_content)

    bucket_results = aggregate_into_buckets(detector_results)

    # save the skills/buckets to the database
    for bucket_name, bucket_data in bucket_results.items():
        insert_project_skill(
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            skill_name=bucket_name,
            level=bucket_data["level"],
            score=bucket_data["score"],
            evidence=json.dumps(bucket_data["evidence"])
        )

    conn.commit()
    print(f"[SKILL EXTRACTION] Completed code skill extraction for: {project_name}")


def _get_zip_name(conn, user_id: int, project_name: str) -> str:
    """
    Get the zip_name for a project from the database.

    Args:
        conn: Database connection
        user_id: User ID
        project_name: Project name

    Returns:
        zip_name string, or None if not found
    """
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT zip_name FROM project_classifications
            WHERE user_id = ? AND project_name = ?
            LIMIT 1
        """, (user_id, project_name))

        result = cursor.fetchone()
        return result[0] if result else None
    except Exception as e:
        print(f"[SKILL EXTRACTION] Error querying zip_name: {e}")
        return None


def _load_file_contents(files: List[Dict], zip_name: str) -> List[Dict]:
    """
    Load file contents from disk and add to each file dict.

    Args:
        files: List of file dicts from database with 'file_path' and 'file_name'
        zip_name: Name of the ZIP file (used to construct base path)

    Returns:
        Same list with 'content' field added to each file dict
    """
    # Determine base path for files (src/analysis/zip_data/{zip_name}/)
    # From src/analysis/skills/flows/code_skill_extraction.py -> go up 4 levels to src/
    current_file = os.path.abspath(__file__)
    # flows/ -> skills/ -> analysis/ -> src/
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
    zip_data_dir = os.path.join(src_dir, "analysis", "zip_data", zip_name)

    files_with_content = []
    loaded_count = 0
    skipped_count = 0

    for file_info in files:
        file_path = file_info.get("file_path", "")
        file_name = file_info.get("file_name", "")

        if not file_path:
            print(f"[SKILL EXTRACTION] Warning: No file_path for {file_name}, skipping")
            skipped_count += 1
            continue

        # Construct absolute path
        absolute_path = os.path.join(zip_data_dir, file_path)

        # Load content
        content = read_file_content(absolute_path)

        if content is not None:
            # Add content to file dict
            file_with_content = file_info.copy()
            file_with_content["content"] = content
            files_with_content.append(file_with_content)
            loaded_count += 1
        else:
            # File couldn't be read, skip it
            skipped_count += 1

    if loaded_count > 0:
        print(f"[SKILL EXTRACTION] Loaded content for {loaded_count} file(s)")
    if skipped_count > 0:
        print(f"[SKILL EXTRACTION] Skipped {skipped_count} file(s) (read error or missing path)")

    return files_with_content


# detector phase
def run_all_code_detectors(files) -> Dict[str, Dict]:
    """
    Runs all registered detector functions over all code files.

    Returns:
        {
            'detector_name': {
                'hits': int,
                'evidence': [ { file, line, snippet }, ... ]
            },
            ...
        }
    """

    results = {name: {"hits": 0, "evidence": []} for name in CODE_DETECTOR_FUNCTIONS}

    for file in files:
        file_text = file.get("content", "")
        file_name = file.get("file_name", "")

        for detector_name, detector_fn in CODE_DETECTOR_FUNCTIONS.items():
            hit, evidence_list = detector_fn(file_text, file_name)

            if hit:
                results[detector_name]["hits"] += 1
                results[detector_name]["evidence"].extend(evidence_list)

    return results


# aggregate buckets
def aggregate_into_buckets(detector_results: Dict[str, Dict]):
    """Convert raw detector output into bucket-level skill scores + evidence."""

    bucket_output = {}

    for bucket in CODE_SKILL_BUCKETS:
        signals_found = 0
        bucket_evidence = []

        for detector_name in bucket.detectors:
            if detector_name in detector_results:
                if detector_results[detector_name]["hits"] > 0:
                    signals_found += 1
                    bucket_evidence.extend(detector_results[detector_name]["evidence"])

        score = signals_found / bucket.total_signals
        level = score_to_level(score)

        bucket_output[bucket.name] = {
            "score": score,
            "level": level,
            "evidence": bucket_evidence,
        }

    return bucket_output