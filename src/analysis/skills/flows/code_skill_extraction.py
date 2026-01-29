import json
import os
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.analysis.skills.utils.skill_levels import score_to_level
from src.analysis.skills.detectors.code.code_detector_registry import CODE_DETECTOR_FUNCTIONS
from src.analysis.skills.buckets.code_buckets import CODE_SKILL_BUCKETS
from src.db import insert_project_skill
from src.utils.helpers import read_file_content
from src.utils.extension_catalog import code_extensions

try:
    from src.db.project_feedback import upsert_project_feedback
except Exception:
    upsert_project_feedback = None

try:
    from src import constants
except ModuleNotFoundError:
    import constants
    
_DETECTOR_FEEDBACK: Dict[str, Dict[str, str]] = {
    "detect_classes": {
        "label": "Use class-based design where appropriate",
        "suggestion": "Introduce classes to encapsulate state/behavior (e.g., domain models, services) instead of purely script-style code."
    },
    "detect_inheritance": {
        "label": "Demonstrate inheritance/abstraction (when appropriate)",
        "suggestion": "Use inheritance or interfaces/abstract base classes to share behavior across related types (only if it improves design)."
    },
    "detect_polymorphism": {
        "label": "Show polymorphism/overrides (when appropriate)",
        "suggestion": "Implement overridden methods or polymorphic interfaces (e.g., @Override, abstract methods) to demonstrate extensible design."
    },
    "detect_hash_maps": {
        "label": "Use dictionary/map data structures",
        "suggestion": "Use dict/Map/HashMap for key→value lookups (e.g., caching, indexing, frequency counts) where it simplifies logic."
    },
    "detect_sets": {
        "label": "Use set-based operations",
        "suggestion": "Use sets for uniqueness checks and fast membership testing (e.g., visited nodes, deduplication, permission scopes)."
    },
    "detect_queues_or_stacks": {
        "label": "Use stack/queue patterns (when suitable)",
        "suggestion": "Use stacks/queues/deques for DFS/BFS, backtracking, scheduling, or producer/consumer style workflows."
    },
    "detect_recursion": {
        "label": "Demonstrate recursion (when suitable)",
        "suggestion": "Implement a recursive solution for naturally recursive problems (trees, DFS, divide-and-conquer) and document base cases."
    },
    "detect_sorting_or_search": {
        "label": "Use sorting/searching patterns",
        "suggestion": "Use sorting or search utilities (sorted/.sort/binary search) when you need ordering, ranking, or efficient retrieval."
    },
    "detect_large_functions": {
        "label": "Improve decomposition for large functions",
        "suggestion": "Split very large functions into smaller helpers (single responsibility) to improve readability, testability, and reuse."
    },
    "detect_comments_docstrings": {
        "label": "Add documentation/comments",
        "suggestion": "Add docstrings/comments for non-obvious logic and public APIs; document inputs/outputs and tricky assumptions."
    },
    "detect_modular_design": {
        "label": "Use modular structure",
        "suggestion": "Refactor into modules/packages and use imports to separate concerns (e.g., db, services, utils, routes)."
    },
    "detect_test_files": {
        "label": "Add test coverage",
        "suggestion": "Add unit/integration tests (e.g., pytest/unittest) under a tests/ folder and cover key edge cases."
    },
    "detect_ci_workflows": {
        "label": "Add CI workflows",
        "suggestion": "Add a CI pipeline (e.g., GitHub Actions) to run formatting/linting/tests automatically on pushes and PRs."
    },
    "detect_assertions": {
        "label": "Use assertions in tests",
        "suggestion": "Add explicit assertions/expectations in tests to validate outputs, error conditions, and invariants."
    },
    "detect_mocking_or_fixtures": {
        "label": "Use fixtures/mocking in tests",
        "suggestion": "Use fixtures/mocks for isolation (e.g., patch external calls, seed test DB/state) to keep tests deterministic."
    },
    "detect_error_handling": {
        "label": "Add robust error handling",
        "suggestion": "Use try/except (or language equivalents) around IO/network/DB operations and raise clear, actionable errors."
    },
    "detect_input_validation": {
        "label": "Validate inputs",
        "suggestion": "Validate user/config/API inputs (schemas, validators, sanitize) and fail fast with clear messages."
    },
    "detect_env_variable_usage": {
        "label": "Use environment configuration",
        "suggestion": "Move secrets/config to environment variables (.env) and document required keys; avoid hardcoding secrets."
    },
    "detect_crypto_usage": {
        "label": "Demonstrate security primitives (when relevant)",
        "suggestion": "Use hashing/encryption/token verification where appropriate (password hashing, JWT validation, secure storage)."
    },
    "detect_mvc_folders": {
        "label": "Use a structured architecture (if applicable)",
        "suggestion": "Organize code into layers (models/views/controllers or equivalents) to separate data, UI, and logic concerns."
    },
    "detect_api_routes": {
        "label": "Expose API routes/endpoints (if applicable)",
        "suggestion": "Implement basic API endpoints (e.g., REST routes) and structure routing cleanly (router/app.get/post)."
    },
    "detect_components": {
        "label": "Frontend components (if applicable)",
        "suggestion": "Add UI components (React/Vue/etc.) or component structure if this project includes a frontend."
    },
    "detect_serialization": {
        "label": "Use serialization/data interchange",
        "suggestion": "Serialize/deserialize data (JSON, DTOs) for persistence or API boundaries and validate formats."
    },
    "detect_database_queries": {
        "label": "Demonstrate DB interactions (if applicable)",
        "suggestion": "Add DB read/write operations (SQL/ORM) for persistence and ensure queries are parameterized."
    },
    "detect_caching": {
        "label": "Use caching (if applicable)",
        "suggestion": "Add caching (lru_cache/Redis/memoization) where repeated computations or reads benefit from it."
    },
}

def _emit_feedback(
    feedback_ctx: Optional[Dict[str, Any]],
    *,
    skill_name: str,
    file_name: str,
    criterion_key: str,
    criterion_label: str,
    expected: str,
    observed: Dict[str, Any],
    suggestion: str,
) -> None:
    """Same shape/pattern as text_detectors.py (callback-first, DB fallback)."""
    if not feedback_ctx:
        return

    cb = feedback_ctx.get("add_feedback")
    if callable(cb):
        cb(
            skill_name,
            file_name,
            criterion_key,
            criterion_label,
            expected,
            observed,
            suggestion,
        )
        return

    if upsert_project_feedback is None:
        return

    conn = feedback_ctx.get("conn")
    user_id = feedback_ctx.get("user_id")
    project_name = feedback_ctx.get("project_name")
    project_type = feedback_ctx.get("project_type") or "code"

    if conn is None or user_id is None or not project_name:
        return

    upsert_project_feedback(
        conn=conn,
        user_id=int(user_id),
        project_name=str(project_name),
        project_type=str(project_type),
        skill_name=str(skill_name),
        file_name=str(file_name or ""),
        criterion_key=str(criterion_key),
        criterion_label=str(criterion_label),
        expected=str(expected),
        observed=observed or {},
        suggestion=str(suggestion),
    )

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
        
    feedback_ctx: Optional[Dict[str, Any]] = None
    if upsert_project_feedback is not None and conn is not None:
        def _add_feedback(
            skill_name: str,
            file_name: str,
            criterion_key: str,
            criterion_label: str,
            expected: str,
            observed: Dict[str, Any],
            suggestion: str,
        ) -> None:
            upsert_project_feedback(
                conn=conn,
                user_id=int(user_id),
                project_name=str(project_name),
                project_type="code",
                skill_name=str(skill_name),
                file_name=str(file_name or ""),
                criterion_key=str(criterion_key),
                criterion_label=str(criterion_label),
                expected=str(expected),
                observed=observed or {},
                suggestion=str(suggestion),
            )

        feedback_ctx = {
            "conn": conn,
            "user_id": user_id,
            "project_name": project_name,
            "project_type": "code",
            "add_feedback": _add_feedback,
        }

    # Get zip_name to construct correct file paths
    zip_name = _get_zip_name(conn, user_id, project_name)
    if not zip_name:
        if constants.VERBOSE:
            print(f"[SKILL EXTRACTION] Warning: Could not determine zip_name for {project_name}, skipping")
        return

    # Filter files before processing (skip non-code and very large files)
    code_exts = code_extensions()
    filtered_files = _filter_code_files(files, code_exts)
    
    # If no code files, emit a single “general” feedback row (mirrors text no-content feedback)
    if not filtered_files:
        _emit_feedback(
            feedback_ctx,
            skill_name="general",
            file_name="",
            criterion_key="code.no_code_files",
            criterion_label="Include supported source code files",
            expected="At least 1 recognized code file (supported extension)",
            observed={"file_count": 0},
            suggestion="Include source files with supported extensions (e.g., .py/.java/.js) so code skills can be detected.",
        )
        return
    
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
    
    _persist_code_feedback(
        feedback_ctx=feedback_ctx,
        detector_results=detector_results,
        bucket_results=bucket_results,
        files_scanned=len(filtered_files),
    )

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

def _persist_code_feedback(
    *,
    feedback_ctx: Optional[Dict[str, Any]],
    detector_results: Dict[str, Dict[str, Any]],
    bucket_results: Dict[str, Dict[str, Any]],
    files_scanned: int,
) -> None:
    """
    Emit feedback rows similar to text: store *unmet* criteria for buckets.
    Minimal-change version: treat each bucket's underlying detectors as criteria.
    """
    if not feedback_ctx:
        return

    # Only emit feedback for buckets that are meaningfully "not hit"
    MIN_BUCKET_SCORE_FOR_NO_FEEDBACK = 0.60  # if bucket >= 0.60, we generally don't nag
    MAX_MISSING_CRITERIA_PER_BUCKET = 3

    for bucket in CODE_SKILL_BUCKETS:
        bname = bucket.name
        bdata = bucket_results.get(bname) or {}
        score = float(bdata.get("score") or 0.0)

        if score >= MIN_BUCKET_SCORE_FOR_NO_FEEDBACK:
            continue

        missing: List[str] = []
        for det in bucket.detectors:
            # Ignore detectors with non-positive weights (if your buckets ever use them)
            if bucket.weights.get(det, 1) <= 0:
                continue
            hits = int((detector_results.get(det) or {}).get("hits") or 0)
            if hits <= 0:
                missing.append(det)

        if not missing:
            continue

        # Prefer higher-weight criteria first
        missing_sorted = sorted(missing, key=lambda d: abs(bucket.weights.get(d, 1)), reverse=True)
        missing_sorted = missing_sorted[:MAX_MISSING_CRITERIA_PER_BUCKET]

        for det in missing_sorted:
            tpl = _DETECTOR_FEEDBACK.get(det) or {}
            label = tpl.get("label") or det.replace("_", " ")
            suggestion = tpl.get("suggestion") or f"Add code evidence that demonstrates: {det.replace('_', ' ')}."

            _emit_feedback(
                feedback_ctx,
                skill_name=bname,
                file_name="",  # bucket-level criterion across project
                criterion_key=f"{bname}.{det}",
                criterion_label=label,
                expected="At least 1 relevant occurrence",
                observed={
                    "hits": 0,
                    "bucket_score": round(score, 3),
                    "files_scanned": int(files_scanned),
                    "detector": det,
                },
                suggestion=suggestion,
            )

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