import json
from typing import Dict, Any, Tuple


def extract_complexity_metrics(
    complexity_summary: Dict[str, Any]
) -> Tuple[int, int, int, int, float, int, float, float, int, int, int, str, str]:
    if not complexity_summary:
        raise ValueError("complexity_summary cannot be empty")

    # Extract basic metrics
    total_files = complexity_summary.get('total_files', 0)
    total_lines = complexity_summary.get('total_lines', 0)
    total_code_lines = complexity_summary.get('total_code', 0)
    total_comments = complexity_summary.get('total_comments', 0)

    # Calculate comment ratio
    comment_ratio = 0.0
    if total_lines > 0:
        comment_ratio = round((total_comments / total_lines) * 100, 2)

    # Extract function and complexity metrics
    total_functions = complexity_summary.get('total_functions', 0)
    avg_complexity = complexity_summary.get('avg_complexity', 0)
    avg_maintainability = complexity_summary.get('avg_maintainability', 0)
    functions_needing_refactor = complexity_summary.get('functions_needing_refactor', 0)
    high_complexity_files = complexity_summary.get('high_complexity_files', 0)
    low_maintainability_files = complexity_summary.get('low_maintainability_files', 0)

    # Serialize JSON details
    radon_details = complexity_summary.get('radon_details', {})
    radon_details_json = json.dumps(radon_details, ensure_ascii=False) if radon_details else json.dumps({})

    lizard_details = complexity_summary.get('lizard_details', {})
    lizard_details_json = json.dumps(lizard_details, ensure_ascii=False) if lizard_details else json.dumps({})

    return (
        total_files,
        total_lines,
        total_code_lines,
        total_comments,
        comment_ratio,
        total_functions,
        avg_complexity,
        avg_maintainability,
        functions_needing_refactor,
        high_complexity_files,
        low_maintainability_files,
        radon_details_json,
        lizard_details_json,
    )