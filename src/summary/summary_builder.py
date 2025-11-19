# src/summaries/summary_builder.py

def build_project_summary(project_obj):
    """
    Takes a CodeProjectMetrics or TextProjectMetrics object and generates a textual summary.
    """
    if hasattr(project_obj, "languages"):
        return summarize_code_project(project_obj)
    else:
        return summarize_text_project(project_obj)

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
