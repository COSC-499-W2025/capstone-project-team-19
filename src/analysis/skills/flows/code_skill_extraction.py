import json
import os
from typing import Dict, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.analysis.skills.utils.skill_levels import score_to_level
from src.analysis.skills.detectors.code.code_detector_registry import CODE_DETECTOR_FUNCTIONS
from src.analysis.skills.buckets.code_buckets import CODE_SKILL_BUCKETS
from src.db import insert_project_skill
from src.utils.helpers import read_file_content
from src.utils.extension_catalog import code_extensions
import src.constants as constants

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

    if constants.VERBOSE:
        print(f"\n[SKILL EXTRACTION] Running CODE skill extraction for {project_name}")

    # Get zip_name to construct correct file paths
    zip_name = _get_zip_name(conn, user_id, project_name)
    if not zip_name:
        if constants.VERBOSE:
            print(f"[SKILL EXTRACTION] Warning: Could not determine zip_name for {project_name}, skipping")
        return

    # Filter files before processing (skip non-code and very large files)
    code_exts = code_extensions()
    filtered_files = _filter_code_files(files, code_exts)
    
    # Run filename-only detectors first (don't need content)
    filename_detectors = ["detect_test_files", "detect_ci_workflows", "detect_mvc_folders"]
    detector_results = run_filename_detectors(filtered_files, filename_detectors)
    
    # Load file contents for content-based detectors
    files_with_content = _load_file_contents(filtered_files, zip_name)

    # Run content-based detectors
    content_detector_results = run_all_code_detectors(files_with_content)
    
    # Merge results
    for detector_name, data in content_detector_results.items():
        detector_results[detector_name] = data

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

    if constants.VERBOSE:
        print(f"[SKILL EXTRACTION] Completed code skill extraction for: {project_name}")


def _filter_code_files(files: List[Dict], code_extensions: set) -> List[Dict]:
    """Filter files to only include code files and exclude very large files."""
    filtered = []
    for file in files:
        file_name = file.get("file_name", "")
        file_path = file.get("file_path", "")
        
        # Skip if no filename
        if not file_name:
            continue
        
        # Check extension
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in code_extensions:
            continue
        
        # Skip very large files (>1MB) - unlikely to be source code
        # Note: We can't check size here without file path, but _load_single_file will handle it
        filtered.append(file)
    
    return filtered

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
        if constants.VERBOSE:
            print(f"[SKILL EXTRACTION] Error querying zip_name: {e}")
        return None

def _load_single_file(file_info, zip_data_dir):
    """Read one file safely, return enriched dict or None."""
    file_path = file_info.get("file_path", "")
    file_name = file_info.get("file_name", "")

    if not file_path: return None

    absolute_path = os.path.join(zip_data_dir, file_path)
    
    # Skip very large files (>1MB) - unlikely to be source code
    try:
        if os.path.getsize(absolute_path) > 1024 * 1024:  # 1MB
            return None
    except OSError:
        pass
    
    content = read_file_content(absolute_path)
    
    if content is None: return None

    file_with_content = file_info.copy()
    file_with_content["content"] = content
    return file_with_content

def _load_file_contents(files: List[Dict], zip_name: str) -> List[Dict]:
    """
    Load file contents in parallel using a  ThreadPoolExecutor
    Mcuh faster for large repos with many small files
    """

    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
    zip_data_dir = os.path.join(src_dir, "analysis", "zip_data", zip_name)

    files_with_content = []
    loaded_count = 0
    skipped_count = 0

    with ThreadPoolExecutor(max_workers=os.cpu_count() * 4) as executor:
        futures = {executor.submit(_load_single_file, f, zip_data_dir): f for f in files}
        for future in as_completed(futures):
            result = future.result()
            if result:
                files_with_content.append(result)
                loaded_count += 1
            else:
                skipped_count += 1

    if constants.VERBOSE:
        print(f"[SKILL EXTRACTION] Loaded content for {loaded_count} file(s)")
    if skipped_count > 0:
        if constants.VERBOSE:
            print(f"[SKILL EXTRACTION] Skipped {skipped_count} file(s) (read error or missing path)")

    return files_with_content

# detector phase - filename-only detectors
def run_filename_detectors(files: List[Dict], detector_names: List[str]) -> Dict[str, Dict]:
    """Run detectors that only need filename, not content."""
    results = {name: {"hits": 0, "evidence": []} for name in detector_names}
    
    for file in files:
        file_name = file.get("file_name", "")
        
        for detector_name in detector_names:
            if detector_name in CODE_DETECTOR_FUNCTIONS:
                detector_fn = CODE_DETECTOR_FUNCTIONS[detector_name]
                # Pass empty lines list since these detectors only use filename
                hit, evidence_list = detector_fn([], file_name)
                
                if hit:
                    results[detector_name]["hits"] += 1
                    results[detector_name]["evidence"].extend(evidence_list)
    
    return results

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

    # Skip filename-only detectors (already processed)
    filename_detectors = {"detect_test_files", "detect_ci_workflows", "detect_mvc_folders"}
    content_detectors = {name: fn for name, fn in CODE_DETECTOR_FUNCTIONS.items() 
                        if name not in filename_detectors}
    
    results = {name: {"hits": 0, "evidence": []} for name in content_detectors}
    
    # Pre-process files: filter out small files and pre-split lines
    processed_files = []
    for file in files:
        file_text = file.get("content", "")
        file_name = file.get("file_name", "")
        
        if not file_text:
            continue
        
        lines = file_text.split("\n")
        
        # Skip very small files (< 3 lines) - unlikely to have patterns
        if len(lines) < 3:
            continue
        
        # Pre-filter empty/whitespace lines for faster processing
        non_empty_lines = [(i, line) for i, line in enumerate(lines, 1) if line.strip()]
        
        if not non_empty_lines:
            continue  # Skip files with only empty lines
        
        # Pre-compute comment line indices for fast O(1) lookup
        from src.analysis.skills.detectors.code.code_detectors import _is_comment_line
        comment_line_indices = {i for i, line in non_empty_lines if _is_comment_line(line)}
        
        processed_files.append({
            "file_name": file_name,
            "lines": lines,
            "comment_line_indices": comment_line_indices  # Fast lookup set
        })
    
    # Batch scanning: for each detector, scan all files
    for detector_name, detector_fn in content_detectors.items():
        for file_data in processed_files:
            # Temporarily attach comment indices to lines for fast checking
            # (detectors can use file_data["comment_line_indices"] if they want)
            hit, evidence_list = detector_fn(file_data["lines"], file_data["file_name"])
            
            if hit:
                results[detector_name]["hits"] += 1
                results[detector_name]["evidence"].extend(evidence_list)

    return results


# aggregate buckets
def aggregate_into_buckets(detector_results: Dict[str, Dict]):
    """Convert raw detector output into bucket-level skill scores + evidence."""

    bucket_output = {}

    for bucket in CODE_SKILL_BUCKETS:
        weighted_signals = 0
        bucket_evidence = []

        # Calculate max possible score (only count positive detectors)
        max_score = sum(1 for d in bucket.detectors if bucket.weights.get(d, 1) > 0)
        if max_score == 0:
            max_score = bucket.total_signals  # fallback if no weights defined

        for detector_name in bucket.detectors:
            if detector_name in detector_results:
                if detector_results[detector_name]["hits"] > 0:
                    # Apply weight (default to +1 if not specified)
                    weight = bucket.weights.get(detector_name, 1)
                    weighted_signals += weight
                    bucket_evidence.extend(detector_results[detector_name]["evidence"])

        # Clamp weighted_signals to [0, max_score] and normalize
        weighted_signals = max(0, min(weighted_signals, max_score))
        score = weighted_signals / max_score if max_score > 0 else 0
        level = score_to_level(score)

        bucket_output[bucket.name] = {
            "score": score,
            "level": level,
            "evidence": bucket_evidence,
        }

    return bucket_output