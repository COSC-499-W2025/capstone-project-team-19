import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Set

from src.analysis.skills.buckets.code_buckets import CODE_SKILL_BUCKETS
from src.analysis.skills.detectors.code.code_detector_registry import CODE_DETECTOR_FUNCTIONS
from src.analysis.skills.flows.code_feedback_templates import _DETECTOR_FEEDBACK
from src.analysis.skills.utils.skill_levels import score_to_level
from src.db import insert_project_skill, upsert_project_feedback
from src.utils.extension_catalog import code_extensions
from src.utils.helpers import read_file_content

try:
    from src import constants
except ModuleNotFoundError:
    import constants


# Feedback plumbing (callback-only)
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
    if not callable(cb):
        return

    cb(
        skill_name,
        file_name,
        criterion_key,
        criterion_label,
        expected,
        observed,
        suggestion,
    )


# Main entry
def extract_code_skills(conn, user_id, project_name, classification, files):
    if constants.VERBOSE:
        print(f"\n[SKILL EXTRACTION] Running CODE skill extraction for {project_name}")

    feedback_ctx: Optional[Dict[str, Any]] = None
    if conn is not None:

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

        # callback-only ctx (no dead fallback path)
        feedback_ctx = {"add_feedback": _add_feedback}

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


# Feedback emission 
def _persist_code_feedback(
    *,
    feedback_ctx: Optional[Dict[str, Any]],
    detector_results: Dict[str, Dict[str, Any]],
    bucket_results: Dict[str, Dict[str, Any]],
    files_scanned: int,
) -> None:
    """
    Feedback behavior:
      - Positive-weight detectors: emit feedback when missing (hits == 0).
      - Negative-weight detectors: emit feedback when present (hits > 0).
      - Keep it readable: cap criteria per bucket and per project.
    """
    if not feedback_ctx:
        return

    MAX_MISSING_CRITERIA_PER_BUCKET = 3
    MAX_MISSING_CRITERIA_PER_PROJECT = 15  # prevents overwhelming rows per upload

    emitted = 0

    for bucket in CODE_SKILL_BUCKETS:
        if emitted >= MAX_MISSING_CRITERIA_PER_PROJECT:
            break

        bname = bucket.name
        bdata = bucket_results.get(bname) or {}
        score = float(bdata.get("score") or 0.0)

        # store (detector_name, weight, hits) so we can tailor "expected" and "observed"
        flagged: List[tuple[str, float, int]] = []

        for det in bucket.detectors:
            weight = float(bucket.weights.get(det, 1))
            hits = int((detector_results.get(det) or {}).get("hits") or 0)

            if weight > 0 and hits <= 0:
                # missing a positive signal
                flagged.append((det, weight, hits))
            elif weight < 0 and hits > 0:
                # negative signal present (anti-pattern)
                flagged.append((det, weight, hits))
            else:
                # weight == 0 or condition not met => no feedback
                continue

        if not flagged:
            continue

        # Prefer higher-importance criteria first (abs(weight)), then cap per bucket
        flagged_sorted = sorted(flagged, key=lambda t: abs(t[1]), reverse=True)
        flagged_sorted = flagged_sorted[:MAX_MISSING_CRITERIA_PER_BUCKET]

        for det, weight, hits in flagged_sorted:
            if emitted >= MAX_MISSING_CRITERIA_PER_PROJECT:
                break

            tpl = _DETECTOR_FEEDBACK.get(det) or {}
            label = tpl.get("label") or det.replace("_", " ")
            suggestion = tpl.get("suggestion") or f"Add code evidence that demonstrates: {det.replace('_', ' ')}."

            # Expected depends on detector sign
            expected = "At least 1 relevant occurrence" if weight > 0 else "No occurrences (0 hits)"

            _emit_feedback(
                feedback_ctx,
                skill_name=bname,
                file_name="",  # bucket-level across the project
                criterion_key=f"{bname}.{det}",
                criterion_label=label,
                expected=expected,
                observed={
                    "hits": hits,
                    "bucket_score": round(score, 3),
                    "files_scanned": int(files_scanned),
                    "detector": det,
                    "weight": weight,
                },
                suggestion=suggestion,
            )
            emitted += 1


# Helpers
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


# Detector runners
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


# Bucket aggregation
def aggregate_into_buckets(detector_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    bucket_output: Dict[str, Dict[str, Any]] = {}

    for bucket in CODE_SKILL_BUCKETS:
        weighted_signals = 0.0
        bucket_evidence: List[Dict[str, Any]] = []

        # IMPORTANT: max_score must reflect weights, otherwise one heavy-weight detector can saturate.
        # Minimal fix: sum of positive weights (fallback to count if weights missing)
        pos_weights = [
            float(bucket.weights.get(d, 1))
            for d in bucket.detectors
            if bucket.weights.get(d, 1) > 0
        ]
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