import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set, Tuple

from src.analysis.skills.buckets.code_buckets import CODE_SKILL_BUCKETS
from src.analysis.skills.detectors.code.code_detector_registry import CODE_DETECTOR_FUNCTIONS
from src.analysis.skills.utils.skill_levels import score_to_level
from src.db import insert_project_skill, upsert_project_feedback
from src.utils.extension_catalog import code_extensions
from src.utils.helpers import read_file_content

try:
    from src import constants
except ModuleNotFoundError:
    import constants


# ---------------------------------------------------------------------
# Feedback templates (detector -> label/suggestion)
# ---------------------------------------------------------------------
_DETECTOR_FEEDBACK: Dict[str, Dict[str, str]] = {
    "detect_classes": {
        "label": "Use class-based design where appropriate",
        "suggestion": "Introduce classes to encapsulate state/behavior (e.g., domain models, services) instead of purely script-style code.",
    },
    "detect_inheritance": {
        "label": "Demonstrate inheritance/abstraction (when appropriate)",
        "suggestion": "Use inheritance or interfaces/abstract base classes to share behavior across related types (only if it improves design).",
    },
    "detect_polymorphism": {
        "label": "Show polymorphism/overrides (when appropriate)",
        "suggestion": "Implement overridden methods or polymorphic interfaces (e.g., @Override, abstract methods) to demonstrate extensible design.",
    },
    "detect_hash_maps": {
        "label": "Use dictionary/map data structures",
        "suggestion": "Use dict/Map/HashMap for key→value lookups (e.g., caching, indexing, frequency counts) where it simplifies logic.",
    },
    "detect_sets": {
        "label": "Use set-based operations",
        "suggestion": "Use sets for uniqueness checks and fast membership testing (e.g., visited nodes, deduplication, permission scopes).",
    },
    "detect_queues_or_stacks": {
        "label": "Use stack/queue patterns (when suitable)",
        "suggestion": "Use stacks/queues/deques for DFS/BFS, backtracking, scheduling, or producer/consumer style workflows.",
    },
    "detect_recursion": {
        "label": "Demonstrate recursion (when suitable)",
        "suggestion": "Implement a recursive solution for naturally recursive problems (trees, DFS, divide-and-conquer) and document base cases.",
    },
    "detect_sorting_or_search": {
        "label": "Use sorting/searching patterns",
        "suggestion": "Use sorting or search utilities (sorted/.sort/binary search) when you need ordering, ranking, or efficient retrieval.",
    },
    "detect_large_functions": {
        "label": "Improve decomposition for large functions",
        "suggestion": "Split very large functions into smaller helpers (single responsibility) to improve readability, testability, and reuse.",
    },
    "detect_comments_docstrings": {
        "label": "Add documentation/comments",
        "suggestion": "Add docstrings/comments for non-obvious logic and public APIs; document inputs/outputs and tricky assumptions.",
    },
    "detect_modular_design": {
        "label": "Use modular structure",
        "suggestion": "Refactor into modules/packages and use imports to separate concerns (e.g., db, services, utils, routes).",
    },
    "detect_test_files": {
        "label": "Add test coverage",
        "suggestion": "Add unit/integration tests (e.g., pytest/unittest) under a tests/ folder and cover key edge cases.",
    },
    "detect_ci_workflows": {
        "label": "Add CI workflows",
        "suggestion": "Add a CI pipeline (e.g., GitHub Actions) to run formatting/linting/tests automatically on pushes and PRs.",
    },
    "detect_assertions": {
        "label": "Use assertions in tests",
        "suggestion": "Add explicit assertions/expectations in tests to validate outputs, error conditions, and invariants.",
    },
    "detect_mocking_or_fixtures": {
        "label": "Use fixtures/mocking in tests",
        "suggestion": "Use fixtures/mocks for isolation (e.g., patch external calls, seed test DB/state) to keep tests deterministic.",
    },
    "detect_error_handling": {
        "label": "Add robust error handling",
        "suggestion": "Use try/except (or language equivalents) around IO/network/DB operations and raise clear, actionable errors.",
    },
    "detect_input_validation": {
        "label": "Validate inputs",
        "suggestion": "Validate user/config/API inputs (schemas, validators, sanitize) and fail fast with clear messages.",
    },
    "detect_env_variable_usage": {
        "label": "Use environment configuration",
        "suggestion": "Move secrets/config to environment variables (.env) and document required keys; avoid hardcoding secrets.",
    },
    "detect_crypto_usage": {
        "label": "Demonstrate security primitives (when relevant)",
        "suggestion": "Use hashing/encryption/token verification where appropriate (password hashing, JWT validation, secure storage).",
    },
    "detect_mvc_folders": {
        "label": "Use a structured architecture (if applicable)",
        "suggestion": "Organize code into layers (models/views/controllers or equivalents) to separate data, UI, and logic concerns.",
    },
    "detect_api_routes": {
        "label": "Expose API routes/endpoints (if applicable)",
        "suggestion": "Implement basic API endpoints (e.g., REST routes) and structure routing cleanly (router/app.get/post).",
    },
    "detect_components": {
        "label": "Frontend components (if applicable)",
        "suggestion": "Add UI components (React/Vue/etc.) or component structure if this project includes a frontend.",
    },
    "detect_serialization": {
        "label": "Use serialization/data interchange",
        "suggestion": "Serialize/deserialize data (JSON, DTOs) for persistence or API boundaries and validate formats.",
    },
    "detect_database_queries": {
        "label": "Demonstrate DB interactions (if applicable)",
        "suggestion": "Add DB read/write operations (SQL/ORM) for persistence and ensure queries are parameterized.",
    },
    "detect_caching": {
        "label": "Use caching (if applicable)",
        "suggestion": "Add caching (lru_cache/Redis/memoization) where repeated computations or reads benefit from it.",
    },
}


# ---------------------------------------------------------------------
# Feedback plumbing (same callback-first pattern as text_detectors.py)
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# Main entry
# ---------------------------------------------------------------------
def extract_code_skills(conn, user_id, project_name, classification, files):
    if constants.VERBOSE:
        print(f"\n[SKILL EXTRACTION] Running CODE skill extraction for {project_name}")
        if upsert_project_feedback is None and _UPSERT_IMPORT_ERROR is not None:
            print(
                "[SKILL EXTRACTION] Feedback disabled: failed to import upsert_project_feedback: "
                f"{_UPSERT_IMPORT_ERROR}"
            )

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

    zip_name = _get_zip_name(conn, user_id, project_name)
    if not zip_name:
        if constants.VERBOSE:
            print(
                f"[SKILL EXTRACTION] Warning: Could not determine zip_name for {project_name}, skipping"
            )
        return

    filtered_files = _filter_code_files(files, code_extensions())
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
        if conn is not None:
            conn.commit()
        return

    # 1) Run detectors
    filename_detectors = ["detect_test_files", "detect_ci_workflows", "detect_mvc_folders"]
    detector_results = run_filename_detectors(filtered_files, filename_detectors)

    files_with_content = _load_file_contents(filtered_files, zip_name)
    content_detector_results = run_all_code_detectors(files_with_content)

    detector_results.update(content_detector_results)

    # 2) Aggregate bucket scores
    bucket_results = aggregate_into_buckets(detector_results)

    # 3) Emit feedback (LIKE TEXT): whenever criteria for a bucket are not met.
    #    IMPORTANT CHANGE: DO NOT gate on bucket score.
    _persist_code_feedback(
        feedback_ctx=feedback_ctx,
        detector_results=detector_results,
        bucket_results=bucket_results,
        files_scanned=len(filtered_files),
    )

    # 4) Persist skills
    for bucket_name, bucket_data in bucket_results.items():
        insert_project_skill(
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            skill_name=bucket_name,
            level=bucket_data["level"],
            score=bucket_data["score"],
            evidence=json.dumps(bucket_data["evidence"]),
        )

    conn.commit()

    if constants.VERBOSE:
        print(f"[SKILL EXTRACTION] Completed code skill extraction for: {project_name}")


# ---------------------------------------------------------------------
# Feedback emission (text-like: record unmet criteria)
# ---------------------------------------------------------------------
def _persist_code_feedback(
    *,
    feedback_ctx: Optional[Dict[str, Any]],
    detector_results: Dict[str, Dict[str, Any]],
    bucket_results: Dict[str, Dict[str, Any]],
    files_scanned: int,
) -> None:
    """
    Text-like behavior:
      - For each bucket, treat each detector as a criterion ("at least 1 hit").
      - If the detector is missing, add a feedback row.
      - Keep it readable: limit missing criteria emitted per bucket.
    """
    if not feedback_ctx:
        return

    MAX_MISSING_CRITERIA_PER_BUCKET = 3

    for bucket in CODE_SKILL_BUCKETS:
        bname = bucket.name
        bdata = bucket_results.get(bname) or {}
        score = float(bdata.get("score") or 0.0)

        missing: List[str] = []
        for det in bucket.detectors:
            # Ignore detectors with non-positive weights (if any)
            if bucket.weights.get(det, 1) <= 0:
                continue
            hits = int((detector_results.get(det) or {}).get("hits") or 0)
            if hits <= 0:
                missing.append(det)

        if not missing:
            continue

        # Prefer higher-weight criteria first, then cap
        missing_sorted = sorted(missing, key=lambda d: abs(bucket.weights.get(d, 1)), reverse=True)
        missing_sorted = missing_sorted[:MAX_MISSING_CRITERIA_PER_BUCKET]

        for det in missing_sorted:
            tpl = _DETECTOR_FEEDBACK.get(det) or {}
            label = tpl.get("label") or det.replace("_", " ")
            suggestion = tpl.get("suggestion") or f"Add code evidence that demonstrates: {det.replace('_', ' ')}."

            _emit_feedback(
                feedback_ctx,
                skill_name=bname,
                file_name="",  # bucket-level across the project
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


# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def _filter_code_files(files: List[Dict[str, Any]], code_exts: Set[str]) -> List[Dict[str, Any]]:
    """
    Accept both shapes:
      - {"file_name": "...", "file_path": "..."}
      - {"filename": "...", "filepath": "..."}  (older callers)
    """
    filtered: List[Dict[str, Any]] = []
    for f in files:
        file_name = f.get("file_name") or f.get("filename") or ""
        if not file_name:
            continue

        ext = os.path.splitext(file_name)[1].lower()
        if ext not in code_exts:
            continue

        filtered.append(f)
    return filtered


def _get_zip_name(conn, user_id: int, project_name: str) -> Optional[str]:
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT zip_name
            FROM project_classifications
            WHERE user_id = ? AND project_name = ?
            LIMIT 1
            """,
            (user_id, project_name),
        )
        row = cursor.fetchone()
        return row[0] if row else None
    except Exception as e:
        if constants.VERBOSE:
            print(f"[SKILL EXTRACTION] Error querying zip_name: {e}")
        return None


def _load_single_file(file_info: Dict[str, Any], zip_data_dir: str) -> Optional[Dict[str, Any]]:
    file_path = file_info.get("file_path") or file_info.get("filepath") or ""
    file_name = file_info.get("file_name") or file_info.get("filename") or ""
    if not file_path:
        return None

    absolute_path = os.path.join(zip_data_dir, file_path)

    # Skip very large files (>1MB)
    try:
        if os.path.getsize(absolute_path) > 1024 * 1024:
            return None
    except OSError:
        pass

    content = read_file_content(absolute_path)
    if content is None:
        return None

    out = dict(file_info)
    # Normalize keys expected downstream
    if "file_name" not in out and file_name:
        out["file_name"] = file_name
    if "file_path" not in out and file_path:
        out["file_path"] = file_path
    out["content"] = content
    return out


def _load_file_contents(files: List[Dict[str, Any]], zip_name: str) -> List[Dict[str, Any]]:
    current_file = os.path.abspath(__file__)
    src_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
    zip_data_dir = os.path.join(src_dir, "analysis", "zip_data", zip_name)

    files_with_content: List[Dict[str, Any]] = []
    loaded_count = 0
    skipped_count = 0

    max_workers = (os.cpu_count() or 4) * 4
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
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
            print(f"[SKILL EXTRACTION] Skipped {skipped_count} file(s) (read error or missing path)")

    return files_with_content


# ---------------------------------------------------------------------
# Detector runners
# ---------------------------------------------------------------------
def run_filename_detectors(
    files: List[Dict[str, Any]],
    detector_names: List[str],
) -> Dict[str, Dict[str, Any]]:
    results = {name: {"hits": 0, "evidence": []} for name in detector_names}

    for f in files:
        file_name = f.get("file_name") or f.get("filename") or ""
        for detector_name in detector_names:
            detector_fn = CODE_DETECTOR_FUNCTIONS.get(detector_name)
            if detector_fn is None:
                continue

            # filename-only detectors ignore lines
            hit, evidence_list = detector_fn([], file_name)
            if hit:
                results[detector_name]["hits"] += 1
                results[detector_name]["evidence"].extend(evidence_list)

    return results


def run_all_code_detectors(files: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    filename_detectors = {"detect_test_files", "detect_ci_workflows", "detect_mvc_folders"}
    content_detectors = {
        name: fn for name, fn in CODE_DETECTOR_FUNCTIONS.items() if name not in filename_detectors
    }

    results = {name: {"hits": 0, "evidence": []} for name in content_detectors}

    processed_files: List[Dict[str, Any]] = []
    for f in files:
        file_text = f.get("content") or ""
        file_name = f.get("file_name") or f.get("filename") or ""
        if not file_text:
            continue

        lines = file_text.split("\n")
        if len(lines) < 3:
            continue

        # small speed win: skip empty-only files
        if not any(line.strip() for line in lines):
            continue

        processed_files.append({"file_name": file_name, "lines": lines})

    for detector_name, detector_fn in content_detectors.items():
        for fd in processed_files:
            hit, evidence_list = detector_fn(fd["lines"], fd["file_name"])
            if hit:
                results[detector_name]["hits"] += 1
                results[detector_name]["evidence"].extend(evidence_list)

    return results


# ---------------------------------------------------------------------
# Bucket aggregation
# ---------------------------------------------------------------------
def aggregate_into_buckets(detector_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    bucket_output: Dict[str, Dict[str, Any]] = {}

    for bucket in CODE_SKILL_BUCKETS:
        weighted_signals = 0.0
        bucket_evidence: List[Dict[str, Any]] = []

        # IMPORTANT: max_score must reflect weights, otherwise one heavy-weight detector can saturate.
        # Minimal fix: sum of positive weights (fallback to count if weights missing)
        pos_weights = [float(bucket.weights.get(d, 1)) for d in bucket.detectors if bucket.weights.get(d, 1) > 0]
        max_score = float(sum(pos_weights)) if pos_weights else float(bucket.total_signals or 1)

        for detector_name in bucket.detectors:
            det_data = detector_results.get(detector_name)
            if not det_data:
                continue
            if int(det_data.get("hits") or 0) > 0:
                weight = float(bucket.weights.get(detector_name, 1))
                if weight != 0:
                    weighted_signals += weight
                bucket_evidence.extend(det_data.get("evidence") or [])

        weighted_signals = max(0.0, min(weighted_signals, max_score))
        score = (weighted_signals / max_score) if max_score > 0 else 0.0
        level = score_to_level(score)

        bucket_output[bucket.name] = {"score": score, "level": level, "evidence": bucket_evidence}

    return bucket_output
