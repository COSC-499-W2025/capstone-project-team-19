def score_to_level(score: float) -> str:
    if score < 0.3:
        return "Beginner"
    elif score < 0.7:
        return "Intermediate"
    return "Advanced"

def classify_level(value: float, max_value: float) -> str:
    """
    Classify a value into Beginner/Intermediate/Advanced based on ratio to max.
    
    Used for collaboration skill levels where we have a value and a maximum.
    Returns Beginner if ratio < 0.33, Intermediate if < 0.66, Advanced otherwise.
    """
    if max_value <= 0:
        return "Beginner"
    
    ratio = value / max_value

    if ratio < 0.33:
        return "Beginner"
    elif ratio < 0.66:
        return "Intermediate"
    else:
        return "Advanced"