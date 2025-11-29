from src.models.project_summary import ProjectSummary

import math

def writing_quality_score(ps: ProjectSummary) -> tuple[float, bool]:
    """
    Compute a 0-1 writing quality score for text projects

    Priority:
        - If LLM metrics exist, use LLM's overall_score (already 0-1).
        - Otherwise, fall back to non-LLM readability using a normalized complexity score based on the Flesch-Kincaid grade level.

    Readability Scoring Logic:
        The fallback metric is `reading_level_avg`, a Flesch-Kincaid estimate of writing complexity. 
        Higher reading levels indicate more complex, more advanced writing.

        To avoid penalizing advanced writing and to provide smooth scaling it is normalized using a logarithmic scale:
            normalized = log(reading_level + 1) / log(20)

        This creates scores that increase with complexity but with diminishing returns at high levels. 
        It avoids assumptions about an “ideal” reading grade and ensures that more advanced writing is always rewarded

        Example interpretation:
            reading_level = 4 = low complexity = around 0.45
            reading_level = 8 = moderate = around 0.60
            reading_level = 12 = advanced  = around 0.70
            reading_level = 16 = expert = around 0.78
            reading_level ≥ 20 = capped at 1.0
    """

    text_metrics = ps.metrics.get("text", {})
    if not isinstance(text_metrics, dict):
        return 0.0, False
    
    # LLM
    llm = text_metrics.get("llm")
    if isinstance(llm, dict):
        score = llm.get("overall_score")
        if isinstance(score, (float, int)):
            final_score = max(0.0, min(score, 1.0))  # already normalized when stored
            return final_score, True

    # reading complexity is based on Flesch-Kincaid
    non_llm = text_metrics.get("non_llm")
    if isinstance(non_llm, dict):
        reading_level = non_llm.get("reading_level_avg")
        if isinstance(reading_level, (float, int)):
            # normalize to 0-1
            normalized = min(math.log(reading_level + 1) / math.log(20), 1)
            return normalized, True
        
    # no usable metrics
    return 0.0, False
        
