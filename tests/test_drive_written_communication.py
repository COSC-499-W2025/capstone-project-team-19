from src.analysis.text_collaborative.drive_collaboration.written_communication import compute_written_communication


def test_written_communication_empty():
    result = compute_written_communication([])
    
    assert result["score"] == 0
    assert result["avg_length"] == 0
    assert result["meaningful_ratio"] == 0
    assert result["constructive_ratio"] == 0
    assert result["total_comments"] == 0


def test_written_communication_short_comments():
    comments = ["ok", "nice", "thanks", "looks good"]
    result = compute_written_communication(comments)
    
    lengths = [len(c.strip()) for c in comments]
    avg = sum(lengths) / len(lengths)
    
    assert result["avg_length"] == avg
    assert result["meaningful_ratio"] == 0  # none > 40 chars
    assert result["total_comments"] == 4
    assert 0 <= result["score"] <= 5


def test_written_communication_meaningful_comments():
    comments = [
        "This section could be improved by adding more examples.",
        "Consider restructuring this paragraph for better flow.",
        "Maybe add a conclusion here to tie everything together.",
    ]
    
    result = compute_written_communication(comments)
    
    lengths = [len(c) for c in comments]
    avg = sum(lengths) / len(lengths)
    
    assert result["avg_length"] == avg
    assert result["meaningful_ratio"] == 1.0  # all > 40 chars
    assert result["total_comments"] == 3
    assert result["score"] > 2  # meaningful comments boost score


def test_written_communication_constructive_feedback():
    comments = [
        "I suggest adding more context here to help readers understand the background better.",
        "Consider improving this section by restructuring the paragraphs for better flow and clarity.",
        "Maybe we could restructure this entire section to make it more coherent and easier to follow.",
    ]
    
    result = compute_written_communication(comments)
    
    # All comments have constructive keywords
    assert result["constructive_ratio"] == 1.0
    # Constructive ratio should boost score
    # With longer comments (>40 chars) and constructive keywords, score should be higher
    assert result["score"] > 2


def test_written_communication_mixed():
    comments = [
        "ok",
        "This paragraph needs better organization and clearer examples.",
        "thanks",
        "Consider adding a transition sentence here to improve flow.",
    ]
    
    result = compute_written_communication(comments)
    
    meaningful_count = sum(1 for c in comments if len(c.strip()) > 40)
    assert result["meaningful_ratio"] == meaningful_count / len(comments)
    assert result["total_comments"] == 4
    assert 0 <= result["score"] <= 5

