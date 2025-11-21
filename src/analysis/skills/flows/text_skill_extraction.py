import json
from typing import Dict, List

from src.analysis.skills.utils.skill_levels import score_to_level
from src.analysis.skills.detectors.code.detector_registry import CODE_DETECTOR_FUNCTIONS
from src.analysis.skills.buckets.code_buckets import CODE_SKILL_BUCKETS
from src.db import insert_project_skill


def extract_code_skills(conn, user_id, project_name, classification, files):
    """
    Main entry point for extracting code-related skills from a project.
    Steps:
        1. Run detectors
        2. Aggregate results into skill buckets
        3. Compute skill scores + levels
        4. Save results in the DB
    """

    print(f"\n[SKILL EXTRACTION] Running CODE skill extraction for {project_name}")

    detector_results = run_all_code_detectors(files)

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


def extract_text_skills(conn, user_id, project_name, classification, files):
    pass