import os
import tempfile
from pathlib import Path
import pytest
from src.alt_analyze import (
    extractfile,
    analyze_linguistic_complexity,
    topic_extraction,
    extract_keywords,
    _interpret_reading_level,
)

def test_extractfromtxt():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a test document.\nThis is the second line of text.\nThis is the third line of text.")
        temp_path=f.name

    try:
        text=extractfile(temp_path)
        assert text is not None
        assert "test document." in text
        assert "second line" in text
        assert "third line"
    finally:
        os.unlink(temp_path)

def test_extractfromtxt_empty():
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            temp_path=f.name
        try:
             text=extractfile(temp_path)
             assert text==""
        finally:
             os.unlink(temp_path)

def test_analyze_linguistic_complexity():
    text="The implementation of sophisticated algorithms necessitates comprehensive understanding of computational complexity theory. Contemporary methodologies incorporate various optimization techniques to enhance performance metrics."
    metrics=analyze_linguistic_complexity(text)

    assert metrics ['word_count']==24
    assert metrics ['sentence_count']==2
    assert metrics['char_count']==226
    assert metrics['flesch_kincaid_grade']>10
    assert metrics['reading_level'] in ['College', 'Graduate']
    assert metrics['lexical_diversity']>0

def test_interpret_reading_level():
    assert _interpret_reading_level(3) == "Elementary"
    assert _interpret_reading_level(7) == "Middle School"
    assert _interpret_reading_level(11) == "High School"
    assert _interpret_reading_level(14) == "College"
    assert _interpret_reading_level(18) == "Graduate"

def test_topic_extraction():
    text="The rapid advancement of artificial intelligence is fundamentally reshaping our world. Machine learning, a powerful subset of AI, allows computers to learn from data and improve their performance without explicit programming. Deep learning models, inspired by neural networks, are achieving remarkable feats in image recognition and natural language processing. Researchers are constantly developing new algorithms to make AI systems more efficient, transparent, and trustworthy. The future will likely see an even deeper integration of this intelligent technology into healthcare, finance, and everyday life, creating both incredible opportunities and complex ethical challenges for society to navigate."
    topics=topic_extraction(text, n_topics=3)
    all_topics=[]
    for topic in topics:
        all_topics.extend(topic['words'])

    assert any(word in all_topics for word in ['learning', 'intelligence', 'artificial'])
    assert len(topics) ==3
    assert all('words' in topic for topic in topics)

def test_extract_keywords():
    text = """
    Python programming language. Python is widely used for data science.
    Machine learning in Python. Python libraries for data analysis.
    """
    keywords=extract_keywords(text, n_words=5)
    assert isinstance(keywords, list)
    keywords_str=' '.join(t[0] for t in keywords)
    assert 'python' in keywords_str.lower()