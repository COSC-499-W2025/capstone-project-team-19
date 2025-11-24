import pytest
from src.analysis.text_individual.alt_analyze import (
    analyze_linguistic_complexity,
    _interpret_reading_level,
)

def test_analyze_linguistic_complexity_basic():
    text = (
        "The implementation of sophisticated algorithms necessitates a deep "
        "understanding of computational principles. Modern methodologies use "
        "optimization to improve performance."
    )

    metrics = analyze_linguistic_complexity(text)

    # Basic structural checks
    assert metrics["word_count"] > 0
    assert metrics["sentence_count"] >= 1
    assert metrics["char_count"] == len(text)

    # Derived metrics
    assert metrics["avg_word_length"] > 0
    assert metrics["avg_sentence_length"] > 0
    assert metrics["lexical_diversity"] > 0

    # Reading level should be reasonable
    assert metrics["flesch_kincaid_grade"] >= 0
    assert metrics["reading_level"] in ["Elementary", "Middle School", "High School", "College", "Graduate"]

def test_analyze_linguistic_complexity_empty():
    metrics = analyze_linguistic_complexity("")

    assert metrics["word_count"] == 0
    assert metrics["sentence_count"] == 0
    assert metrics["char_count"] == 0
    assert metrics["avg_word_length"] == 0
    assert metrics["avg_sentence_length"] == 0
    assert metrics["lexical_diversity"] == 0
    assert metrics["reading_level"] == "N/A"

def test_analyze_linguistic_complexity_whitespace_only():
    metrics = analyze_linguistic_complexity("   \n  \t ")
    assert metrics["word_count"] == 0
    assert metrics["reading_level"] == "N/A"

def test_interpret_reading_level():
    assert _interpret_reading_level(3) == "Elementary"
    assert _interpret_reading_level(7) == "Middle School"
    assert _interpret_reading_level(11) == "High School"
    assert _interpret_reading_level(14) == "College"
    assert _interpret_reading_level(18) == "Graduate"