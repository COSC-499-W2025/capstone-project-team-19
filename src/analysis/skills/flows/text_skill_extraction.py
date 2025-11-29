import json
from typing import Dict, List

from src.analysis.skills.utils.skill_levels import score_to_level
from src.analysis.skills.detectors.text.text_detector_registry import TEXT_DETECTOR_FUNCTIONS
from src.analysis.skills.buckets.text_buckets import TEXT_SKILL_BUCKETS
from src.db import insert_project_skill

from src.db.text_metrics import store_text_offline_metrics
from src.analysis.text_individual.alt_analyze import analyze_linguistic_complexity
from src.db import get_classification_id


def extract_text_skills(
    main_text,
    supporting_texts,
    csv_metadata,
    project_name,
    user_id,
    conn,
):
    """
    Runs all detectors, aggregates into buckets, computes overall score,
    stores results in DB, and returns bucket summary for printing.
    """

    # ------------------------------
    # 1. Format files for detectors
    # ------------------------------
    files = [{"file_name": "MAIN", "content": main_text}]
    for s in supporting_texts:
        files.append({"file_name": s["filename"], "content": s["text"]})

    # ------------------------------
    # 2. RUN ALL DETECTORS
    # Each detector returns:
    #     { "score": float, "evidence": [...] }
    # ------------------------------
    detector_results = {}
    for name, fn in TEXT_DETECTOR_FUNCTIONS.items():

        # Pass extra parameters only to relevant detectors
        if name == "detect_iterative_process":
            out = fn(main_text, "MAIN", supporting_files=supporting_texts)
        elif name == "detect_planning_behavior":
            out = fn(main_text, "MAIN", supporting_files=supporting_texts)
        elif name == "detect_data_collection":
            out = fn(main_text, "MAIN", csv_metadata=csv_metadata)
        else:
            out = fn(main_text, "MAIN")

        detector_results[name] = out

    # ------------------------------
    # 3. AGGREGATE INTO BUCKETS
    # bucket score = average of detector scores in bucket
    # ------------------------------
    bucket_output = {}

    for bucket in TEXT_SKILL_BUCKETS:
        bucket_scores = []
        bucket_evidence = []

        for det in bucket.detectors:
            if det in detector_results:
                bucket_scores.append(detector_results[det]["score"])
                bucket_evidence.extend(detector_results[det]["evidence"])

        if bucket_scores:
            score = sum(bucket_scores) / len(bucket_scores)
        else:
            score = 0

        bucket_output[bucket.name] = {
            "description": bucket.description,
            "score": score,
            "evidence": bucket_evidence,
        }

        # Store in DB
        insert_project_skill(
            conn=conn,
            user_id=user_id,
            project_name=project_name,
            skill_name=bucket.name,
            level=score_to_level(score),
            score=score,
            evidence=json.dumps(bucket_evidence),
        )

    conn.commit()

    # ------------------------------
    # 4. OVERALL PROJECT SCORE
    # ------------------------------
    overall_score = sum(b["score"] for b in bucket_output.values()) / len(bucket_output)
    
    classification_id = get_classification_id(conn, user_id, project_name)

    if classification_id:
        ling = analyze_linguistic_complexity(main_text)

        project_metrics = {
            "summary": {
                "total_documents": 1,
                "total_words": ling["word_count"],
                "reading_level_average": ling["flesch_kincaid_grade"],
                "reading_level_label": ling["reading_level"]
            },
            "keywords": [],  # TF-IDF can be added later
        }

        store_text_offline_metrics(conn, classification_id, project_metrics, csv_metadata=csv_metadata)

    return {
        "overall_score": overall_score,
        "buckets": bucket_output
    }
