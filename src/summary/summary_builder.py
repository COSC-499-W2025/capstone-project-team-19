# src/summary/summary_builder.py

from src.summary.metrics_model import CodeProjectMetrics, TextProjectMetrics

def build_project_summary(project_obj):
    """
    Takes a CodeProjectMetrics or TextProjectMetrics object and generates a textual summary.
    """
    if isinstance(project_obj, CodeProjectMetrics):
        return summarize_code_project(project_obj)
    elif isinstance(project_obj, TextProjectMetrics):
        return summarize_text_project(project_obj)
    else:
        raise TypeError(f"Unknown project type: {type(project_obj)}")

def summarize_code_project(obj):
    """
    Produce resume-ready text from code project metrics.
    """
    # TODO: fill in later
    return f"[CODE SUMMARY PLACEHOLDER for {obj.project_name}]"

def summarize_text_project(obj):
    """
    Produce résumé-ready text from text project metrics.
    """
    # TODO: fill in later
    return f"[TEXT SUMMARY PLACEHOLDER for {obj.project_name}]"
