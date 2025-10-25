import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock
from src.alt_analyze import (
    extractfile,
    analyze_linguistic_complexity,
    topic_extraction,
    extract_keywords,
    _interpret_reading_level,
    calculate_document_metrics,
    calculate_project_metrics,
    extractfromtxt,
    extractfrompdf,
    extractfromdocx,
    group_files_by_project,
    ask_user_for_project_summaries,
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

    assert metrics ['word_count']==22
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

def test_extract_keywords_empty_text():
    keywords = extract_keywords("", n_words=5)
    assert keywords == []

def test_topic_extraction_empty_text():
    topics = topic_extraction("", n_topics=3)
    assert topics == []

def test_analyze_linguistic_complexity_empty_text():
    metrics = analyze_linguistic_complexity("")
    assert metrics['word_count'] == 0
    assert metrics['sentence_count'] == 0
    assert metrics['char_count'] == 0
    assert metrics['reading_level'] == 'N/A'

def test_extractfile_unsupported_format():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.xyz', delete=False) as f:
        f.write("This is unsupported format")
        temp_path = f.name

    try:
        text = extractfile(temp_path)
        assert text is None
    finally:
        os.unlink(temp_path)

def test_extractfile_nonexistent():
    result = extractfile("/nonexistent/path/file.txt")
    assert result is None

def test_extractfromtxt_specific():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("Sample text content for testing.")
        temp_path = f.name

    try:
        text = extractfromtxt(temp_path)
        assert text == "Sample text content for testing."
    finally:
        os.unlink(temp_path)

def test_extractfrompdf():
    # Test with real PDF file from tests folder
    tests_dir = Path(__file__).parent
    pdf_path = tests_dir / 'test.pdf'

    if pdf_path.exists():
        text = extractfrompdf(str(pdf_path))
        assert text is not None
        assert len(text) > 0
    else:
        # Fallback: test error handling with non-existent file
        result = extractfrompdf("/nonexistent/file.pdf")
        assert result == ""

def test_extractfromdocx():
    # Test with real DOCX file from tests folder
    tests_dir = Path(__file__).parent
    docx_path = tests_dir / 'test.docx'

    if docx_path.exists():
        text = extractfromdocx(str(docx_path))
        assert text is not None
        assert len(text) > 0
    else:
        # Fallback: test error handling with non-existent file
        result = extractfromdocx("/nonexistent/file.docx")
        assert result is None

def test_extractfrompdf_nonexistent():
    # Test error handling with non-existent PDF
    result = extractfrompdf("/nonexistent/file.pdf")
    assert result == ""

def test_extractfromdocx_nonexistent():
    # Test error handling with non-existent DOCX
    result = extractfromdocx("/nonexistent/file.docx")
    assert result is None

def test_calculate_document_metrics():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("This is a comprehensive test document. It contains multiple sentences to test the analysis. The document should provide meaningful metrics for linguistic complexity and readability analysis.")
        temp_path = f.name

    try:
        metrics = calculate_document_metrics(temp_path)

        assert metrics['processed'] == True
        assert 'linguistic_metrics' in metrics
        assert 'topics' in metrics
        assert 'keywords' in metrics
        assert 'processing_timestamp' in metrics

        # Check linguistic metrics are present
        assert metrics['linguistic_metrics']['word_count'] > 0
        assert metrics['linguistic_metrics']['sentence_count'] > 0

        # Check keywords are limited to 10
        assert len(metrics['keywords']) <= 10
    finally:
        os.unlink(temp_path)

def test_calculate_document_metrics_invalid_file():
    metrics = calculate_document_metrics("/nonexistent/file.txt")

    assert metrics['processed'] == False
    assert 'error' in metrics
    assert metrics['error'] == 'Failed to extract text'

def test_calculate_project_metrics():
    # Create sample document metrics
    doc_metrics = [
        {
            'processed': True,
            'linguistic_metrics': {
                'word_count': 100,
                'sentence_count': 5,
                'flesch_kincaid_grade': 10.5
            },
            'keywords': [('python', 0.8), ('data', 0.6), ('analysis', 0.5)]
        },
        {
            'processed': True,
            'linguistic_metrics': {
                'word_count': 150,
                'sentence_count': 8,
                'flesch_kincaid_grade': 12.3
            },
            'keywords': [('machine', 0.7), ('learning', 0.9), ('python', 0.6)]
        }
    ]

    project_metrics = calculate_project_metrics(doc_metrics)

    assert 'summary' in project_metrics
    assert project_metrics['summary']['total_documents'] == 2
    assert project_metrics['summary']['total_words'] == 250
    assert 'reading_level_average' in project_metrics['summary']
    assert 'reading_level_label' in project_metrics['summary']
    assert 'keywords' in project_metrics

    # Check that keywords are aggregated
    keyword_words = [kw['word'] for kw in project_metrics['keywords']]
    assert 'python' in keyword_words

def test_calculate_project_metrics_empty():
    result = calculate_project_metrics([])
    assert result == {}

def test_calculate_project_metrics_no_valid_docs():
    doc_metrics = [
        {'processed': False, 'error': 'Failed to process'},
        {'processed': False, 'error': 'Failed to process'}
    ]

    result = calculate_project_metrics(doc_metrics)
    assert 'error' in result
    assert result['error'] == 'No documents processed'

def test_topic_extraction_with_short_text():
    text = "Python programming."
    topics = topic_extraction(text, n_topics=5, n_words=3)

    # Should return topics even with short text
    assert isinstance(topics, list)

def test_extract_keywords_with_ngrams():
    text = "Machine learning is a subset of artificial intelligence. Machine learning algorithms learn from data."
    keywords = extract_keywords(text, n_words=10)

    assert isinstance(keywords, list)
    assert len(keywords) > 0

    # Check that we have tuples of (word, score)
    for keyword in keywords:
        assert isinstance(keyword, tuple)
        assert len(keyword) == 2
        assert isinstance(keyword[0], str)
        assert isinstance(keyword[1], float)

def test_analyze_linguistic_complexity_whitespace_only():
    metrics = analyze_linguistic_complexity("   \n\t   ")
    assert metrics['word_count'] == 0
    assert metrics['reading_level'] == 'N/A'

# Tests for new functions added for project summary feature

def test_group_files_by_project_with_root_folder():
    """Test grouping files when there's a single root folder with projects at second level."""
    # Structure: root/project_name/files
    text_files = [
        {'file_path': 'CS101/assignment1/report.txt', 'file_type': 'text'},
        {'file_path': 'CS101/assignment1/code.txt', 'file_type': 'text'},
        {'file_path': 'CS101/assignment2/notes.txt', 'file_type': 'text'},
        {'file_path': 'CS101/group_project/design.txt', 'file_type': 'text'},
        {'file_path': 'CS101/group_project/report.txt', 'file_type': 'text'},
    ]

    # The function calls analyze_project_layout internally, so we need to mock it correctly
    with patch('src.alt_analyze.analyze_project_layout') as mock_layout:
        mock_layout.return_value = {
            'root_name': 'CS101',
            'auto_assignments': {
                'assignment1': 'individual',
                'assignment2': 'individual',
                'group_project': 'collaborative'
            },
            'pending_projects': [],
            'stray_locations': []
        }

        result = group_files_by_project(text_files)

        assert 'assignment1' in result
        assert 'assignment2' in result
        assert 'group_project' in result

        assert len(result['assignment1']) == 2
        assert len(result['assignment2']) == 1
        assert len(result['group_project']) == 2

def test_group_files_by_project_no_root_folder():
    """Test grouping files when there's no root folder."""
    # Structure: project_name/files (no root)
    text_files = [
        {'file_path': 'project1/file.txt', 'file_type': 'text'},
        {'file_path': 'project2/file.txt', 'file_type': 'text'},
    ]

    with patch('src.alt_analyze.analyze_project_layout') as mock_layout:
        mock_layout.return_value = {
            'root_name': None,
            'auto_assignments': {
                'project1': 'individual',
                'project2': 'collaborative'
            },
            'pending_projects': [],
            'stray_locations': []
        }

        result = group_files_by_project(text_files)

        assert 'project1' in result
        assert 'project2' in result
        assert len(result['project1']) == 1
        assert len(result['project2']) == 1

def test_group_files_by_project_no_projects_detected():
    """Test when no projects are detected, should return default project."""
    text_files = [
        {'file_path': 'file1.txt', 'file_type': 'text'},
        {'file_path': 'file2.txt', 'file_type': 'text'},
    ]

    with patch('src.alt_analyze.analyze_project_layout') as mock_layout:
        mock_layout.return_value = {
            'root_name': None,
            'auto_assignments': {},
            'pending_projects': [],
            'stray_locations': []
        }

        result = group_files_by_project(text_files)

        # Should return all files under "Default Project"
        assert 'Default Project' in result
        assert len(result['Default Project']) == 2

def test_group_files_by_project_filters_macosx():
    """Test that __MACOSX files are filtered out."""
    text_files = [
        {'file_path': 'CS101/assignment1/report.txt', 'file_type': 'text'},
        {'file_path': '__MACOSX/assignment1/._report.txt', 'file_type': 'text'},
    ]

    with patch('src.alt_analyze.analyze_project_layout') as mock_layout:
        mock_layout.return_value = {
            'root_name': 'CS101',
            'auto_assignments': {'assignment1': 'individual'},
            'pending_projects': [],
            'stray_locations': []
        }

        result = group_files_by_project(text_files)

        assert 'assignment1' in result
        # Only 1 file should be in assignment1 (MACOSX file filtered out)
        assert len(result['assignment1']) == 1
        assert '__MACOSX' not in result['assignment1'][0]['file_path']

def test_ask_user_for_project_summaries_all_projects():
    """Test asking user for summaries when they provide input for all projects."""
    project_names = ['assignment1', 'assignment2', 'group_project']

    # Mock user input: provides summaries for all projects
    user_inputs = [
        'Built a calculator app',
        'Created a web scraper',
        'Team e-commerce platform'
    ]

    with patch('builtins.input', side_effect=user_inputs):
        result = ask_user_for_project_summaries(project_names)

        assert len(result) == 3
        assert result['assignment1'] == 'Built a calculator app'
        assert result['assignment2'] == 'Created a web scraper'
        assert result['group_project'] == 'Team e-commerce platform'

def test_ask_user_for_project_summaries_skip_some():
    """Test when user skips some projects by pressing Enter."""
    project_names = ['assignment1', 'assignment2', 'assignment3']

    # Mock user input: provides summary for first, skips second, provides for third
    user_inputs = [
        'First project summary',
        '',  # Skip assignment2
        'Third project summary'
    ]

    with patch('builtins.input', side_effect=user_inputs):
        result = ask_user_for_project_summaries(project_names)

        assert len(result) == 2
        assert result['assignment1'] == 'First project summary'
        assert 'assignment2' not in result
        assert result['assignment3'] == 'Third project summary'

def test_ask_user_for_project_summaries_skip_all():
    """Test when user skips all projects."""
    project_names = ['assignment1', 'assignment2']

    # Mock user input: skips all projects
    user_inputs = ['', '']

    with patch('builtins.input', side_effect=user_inputs):
        result = ask_user_for_project_summaries(project_names)

        assert len(result) == 0
        assert result == {}

def test_ask_user_for_project_summaries_empty_list():
    """Test when no projects are provided."""
    result = ask_user_for_project_summaries([])
    assert result == {}

def test_ask_user_for_project_summaries_whitespace_trimmed():
    """Test that whitespace is trimmed from user input."""
    project_names = ['assignment1']

    user_inputs = ['  Trimmed summary  ']

    with patch('builtins.input', side_effect=user_inputs):
        result = ask_user_for_project_summaries(project_names)

        assert result['assignment1'] == 'Trimmed summary'

def test_ask_user_for_project_summaries_whitespace_only_skipped():
    """Test that whitespace-only input is treated as skip."""
    project_names = ['assignment1']

    user_inputs = ['   ']

    with patch('builtins.input', side_effect=user_inputs):
        result = ask_user_for_project_summaries(project_names)

        assert len(result) == 0
        assert 'assignment1' not in result

def test_group_files_by_project_with_pending_projects():
    """Test grouping files with pending (unclassified) projects."""
    text_files = [
        {'file_path': 'root/hw1/file.txt', 'file_type': 'text'},
        {'file_path': 'root/project/file.txt', 'file_type': 'text'},
    ]

    with patch('src.alt_analyze.analyze_project_layout') as mock_layout:
        mock_layout.return_value = {
            'root_name': 'root',
            'auto_assignments': {'hw1': 'individual'},
            'pending_projects': ['project'],
            'stray_locations': []
        }

        result = group_files_by_project(text_files)

        assert 'hw1' in result
        assert 'project' in result
        assert len(result['hw1']) == 1
        assert len(result['project']) == 1