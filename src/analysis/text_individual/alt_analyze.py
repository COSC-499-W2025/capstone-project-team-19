# src/analysis/text_individual/alt_analyze.py

import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
import textstat

def nltk_data():
    required = [
        ('tokenizers/punkt', 'punkt'),
        ('tokenizers/punkt_tab', "punkt_tab"),
        ('corpora/stopwords', 'stopwords'),
    ]

    for path, package in required:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(package, quiet=True)

# Ensure NLTK is ready
nltk_data()


def analyze_linguistic_complexity(text: str):
    """
    Returns:
        {
            'word_count': int,
            'sentence_count': int,
            'char_count': int,
            'avg_word_length': float,
            'avg_sentence_length': float,
            'lexical_diversity': float,
            'flesch_reading_ease': float,
            'flesch_kincaid_grade': float,
            'smog_index': float,
            'reading_level': str
        }
    """

    if not text or not text.strip():
        return {
            'word_count': 0,
            'sentence_count': 0,
            'char_count': 0,
            'avg_word_length': 0,
            'avg_sentence_length': 0,
            'lexical_diversity': 0,
            'flesch_reading_ease': 0,
            'flesch_kincaid_grade': 0,
            'smog_index': 0,
            'reading_level': 'N/A'
        }

    tokens = [w for w in word_tokenize(text) if w.isalpha()]
    words = word_tokenize(text.lower())
    unique_words = set(words)

    word_count = len(tokens)
    sentence_count = len(sent_tokenize(text))
    char_count = len(text)

    lexical_diversity = len(unique_words) / word_count if word_count > 0 else 0

    avg_word_length = char_count / word_count if word_count else 0
    avg_sentence_length = word_count / sentence_count if sentence_count else 0

    return {
        'word_count': word_count,
        'sentence_count': sentence_count,
        'char_count': char_count,
        'avg_word_length': round(avg_word_length, 2),
        'avg_sentence_length': round(avg_sentence_length, 2),
        'lexical_diversity': round(lexical_diversity, 3),
        'flesch_reading_ease': round(textstat.flesch_reading_ease(text), 2),
        'flesch_kincaid_grade': round(textstat.flesch_kincaid_grade(text), 2),
        'smog_index': round(textstat.smog_index(text), 2),
        'reading_level': _interpret_reading_level(textstat.flesch_kincaid_grade(text))
    }


def _interpret_reading_level(grade: float):
    if grade < 6:
        return "Elementary"
    elif grade < 9:
        return "Middle School"
    elif grade < 13:
        return "High School"
    elif grade < 16:
        return "College"
    else:
        return "Graduate"


