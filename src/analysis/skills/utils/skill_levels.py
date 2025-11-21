def score_to_level(score: float) -> str:
    if score < 0.3:
        return "Beginner"
    elif score < 0.7:
        return "Intermediate"
    return "Advanced"