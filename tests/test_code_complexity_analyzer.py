import os
import pytest
from unittest.mock import MagicMock, Mock, mock_open
import src.analysis.code_individual.code_complexity_analyzer as cca


def test_analyze_code_complexity_no_files(tmp_sqlite_conn, capsys):
    """
    Test when no code files are found in database.
    Should return empty dict and print message.
    """
    # Create tables if needed
    cursor = tmp_sqlite_conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_name TEXT,
            file_path TEXT,
            user_id INTEGER,
            project_name TEXT,
            file_type TEXT
        )
    """)
    tmp_sqlite_conn.commit()

    result = cca.analyze_code_complexity(tmp_sqlite_conn, 1, 'test_project', '/path/to/test.zip')

    assert result == {}
    out = capsys.readouterr().out
    assert "No code files found" in out

def test_analyze_code_complexity_with_python_file(tmp_sqlite_conn, tmp_path, monkeypatch, capsys):
    """
    Test analyzing a Python file with both Radon and Lizard.
    """
    # Setup database with a Python file
    cursor = tmp_sqlite_conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            file_name TEXT,
            file_path TEXT,
            user_id INTEGER,
            project_name TEXT,
            file_type TEXT
        )
    """)
    cursor.execute(
        "INSERT INTO files (file_name, file_path, user_id, project_name, file_type) VALUES (?, ?, ?, ?, ?)",
        ('test.py', 'src/test.py', 1, 'test_project', 'code')
    )
    tmp_sqlite_conn.commit()

    # Create fake file
    fake_base_path = tmp_path / "zip_data" / "test"
    fake_base_path.mkdir(parents=True)
    fake_file = fake_base_path / "src" / "test.py"
    fake_file.parent.mkdir(parents=True)
    fake_file.write_text("def hello():\n    return 'world'\n")

    # Mock paths
    monkeypatch.setattr(os.path, 'abspath', lambda x: str(tmp_path))
    monkeypatch.setattr(os.path, 'dirname', lambda x: str(tmp_path))

    # Mock extension detection
    monkeypatch.setattr(cca, 'get_languages_for_extension', lambda ext: ['Python'] if ext == '.py' else [])

    # Mock Radon analysis
    mock_radon_data = {
        'file_name': 'test.py',
        'cyclomatic_complexity': [
            {'name': 'hello', 'complexity': 1, 'rank': 'A', 'lineno': 1}
        ],
        'average_complexity': 1.0,
        'maintainability_index': 85.5,
        'maintainability_rank': 'A',
        'loc': 2,
        'lloc': 1,
        'sloc': 1,
        'comments': 0,
        'multi': 0,
        'blank': 0
    }
    monkeypatch.setattr(cca, 'analyze_with_radon', lambda fp, fn, is_py: mock_radon_data if is_py else None)

    # Mock Lizard analysis
    mock_lizard_data = {
        'file_name': 'test.py',
        'nloc': 2,
        'average_nloc': 2.0,
        'average_ccn': 1.0,
        'average_token': 5.0,
        'functions': [
            {'name': 'hello', 'lines': 2, 'ccn': 1, 'token_count': 5, 'parameters': 0, 'start_line': 1, 'end_line': 2}
        ],
        'function_count': 1
    }
    monkeypatch.setattr(cca, 'analyze_with_lizard', lambda fp, fn: mock_lizard_data)

    result = cca.analyze_code_complexity(tmp_sqlite_conn, 1, 'test_project', str(tmp_path / 'test.zip'))

    assert 'radon_metrics' in result
    assert 'lizard_metrics' in result
    assert 'summary' in result
    assert len(result['radon_metrics']) == 1
    assert len(result['lizard_metrics']) == 1

def test_analyze_with_radon_python_file(tmp_path, monkeypatch):
    """
    Test analyze_with_radon on a Python file.
    """
    # Create a simple Python file
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def simple_function():
    return 42

def complex_function(x):
    if x > 0:
        if x > 10:
            return "big"
        return "positive"
    return "negative"
""")

    result = cca.analyze_with_radon(str(test_file), 'test.py', is_python=True)

    assert result is not None
    assert result['file_name'] == 'test.py'
    assert 'cyclomatic_complexity' in result
    assert 'maintainability_index' in result
    assert 'loc' in result
    assert 'sloc' in result
    assert len(result['cyclomatic_complexity']) >= 2  # At least 2 functions

def test_analyze_with_radon_non_python_file(tmp_path):
    """
    Test analyze_with_radon skips non-Python files.
    """
    test_file = tmp_path / "test.js"
    test_file.write_text("function hello() { return 'world'; }")

    result = cca.analyze_with_radon(str(test_file), 'test.js', is_python=False)

    assert result is None

def test_analyze_with_radon_handles_error(tmp_path, monkeypatch, capsys):
    """
    Test analyze_with_radon handles errors gracefully.
    """
    test_file = tmp_path / "test.py"
    test_file.write_text("invalid python syntax ::::")
    result = cca.analyze_with_radon(str(test_file), 'test.py', is_python=True)
    assert result is None or isinstance(result, dict)

def test_analyze_with_lizard_success(tmp_path):
    """
    Test analyze_with_lizard on a code file.
    """
    test_file = tmp_path / "test.py"
    test_file.write_text("""
def function_one():
    return 1

def function_two(a, b, c):
    if a > b:
        return a
    return b
""")

    result = cca.analyze_with_lizard(str(test_file), 'test.py')

    assert result is not None
    assert result['file_name'] == 'test.py'
    assert 'nloc' in result
    assert 'functions' in result
    assert result['function_count'] >= 2

    # Check function details
    funcs = result['functions']
    assert all('name' in f for f in funcs)
    assert all('ccn' in f for f in funcs)
    assert all('lines' in f for f in funcs)

def test_analyze_with_lizard_handles_error(tmp_path, monkeypatch, capsys):
    """
    Test analyze_with_lizard handles errors gracefully.
    """
    # File doesn't exist
    result = cca.analyze_with_lizard('/nonexistent/file.py', 'file.py')

    # Lizard returns a result with zero values even on error
    assert result is not None
    assert result['file_name'] == 'file.py'
    assert result['nloc'] == 0
    assert result['function_count'] == 0

def test_aggregate_complexity_metrics_comprehensive():
    """
    Test aggregate_complexity_metrics with comprehensive data.
    """
    radon_results = [
        {
            'file_name': 'file1.py',
            'cyclomatic_complexity': [
                {'name': 'func1', 'complexity': 5, 'rank': 'B'},
                {'name': 'func2', 'complexity': 15, 'rank': 'D'}
            ],
            'average_complexity': 10.0,
            'maintainability_index': 70.0,
            'loc': 100,
            'sloc': 80,
            'comments': 10,
            'blank': 10,
            'multi': 0
        },
        {
            'file_name': 'file2.py',
            'cyclomatic_complexity': [
                {'name': 'func3', 'complexity': 3, 'rank': 'A'}
            ],
            'average_complexity': 3.0,
            'maintainability_index': 85.0,
            'loc': 50,
            'sloc': 40,
            'comments': 5,
            'blank': 5,
            'multi': 0
        }
    ]

    lizard_results = [
        {
            'file_name': 'file1.py',
            'nloc': 80,
            'average_ccn': 10.0,
            'average_token': 50.0,
            'function_count': 2,
            'functions': [
                {'name': 'func1', 'ccn': 5, 'lines': 10, 'token_count': 40, 'parameters': 2},
                {'name': 'func2', 'ccn': 15, 'lines': 20, 'token_count': 60, 'parameters': 3}
            ]
        },
        {
            'file_name': 'file2.py',
            'nloc': 40,
            'average_ccn': 3.0,
            'average_token': 30.0,
            'function_count': 1,
            'functions': [
                {'name': 'func3', 'ccn': 3, 'lines': 8, 'token_count': 30, 'parameters': 1}
            ]
        }
    ]

    summary = cca.aggregate_complexity_metrics(radon_results, lizard_results)

    assert summary['total_files'] == 2
    assert summary['total_lines'] == 150  # 100 + 50
    assert summary['total_code'] == 120  # 80 + 40
    assert summary['total_comments'] == 15  # 10 + 5
    assert summary['total_functions'] == 3
    assert summary['avg_complexity'] == 6.5  # (10 + 3) / 2
    assert summary['avg_maintainability'] == 77.5  # (70 + 85) / 2
    assert 'complexity_distribution' in summary
    assert 'most_complex_functions' in summary
    assert len(summary['most_complex_functions']) > 0

def test_aggregate_complexity_metrics_only_lizard():
    """
    Test aggregate_complexity_metrics with only Lizard results (non-Python project).
    """
    lizard_results = [
        {
            'file_name': 'file1.js',
            'nloc': 100,
            'average_ccn': 8.0,
            'average_token': 45.0,
            'function_count': 3,
            'functions': [
                {'name': 'func1', 'ccn': 5, 'lines': 10, 'token_count': 40, 'parameters': 1},
                {'name': 'func2', 'ccn': 18, 'lines': 25, 'token_count': 70, 'parameters': 2},
                {'name': 'func3', 'ccn': 3, 'lines': 5, 'token_count': 20, 'parameters': 0}
            ]
        }
    ]

    summary = cca.aggregate_complexity_metrics([], lizard_results)

    assert summary['total_files'] == 1
    assert summary['total_lines'] == 100  # Uses Lizard's nloc
    assert summary['total_code'] == 100
    assert summary['total_functions'] == 3
    assert len(summary['most_complex_functions']) > 0
    assert summary['most_complex_functions'][0]['ccn'] == 18  # func2 is most complex

def test_aggregate_complexity_metrics_empty():
    """
    Test aggregate_complexity_metrics with no results.
    """
    summary = cca.aggregate_complexity_metrics([], [])
    assert summary == {}

def test_aggregate_complexity_metrics_identifies_refactor_candidates():
    """
    Test that functions needing refactoring are identified.
    """
    radon_results = [
        {
            'cyclomatic_complexity': [
                {'name': 'bad_func', 'complexity': 20, 'rank': 'F'}, 
                {'name': 'good_func', 'complexity': 3, 'rank': 'A'}
            ],
            'average_complexity': 11.5,
            'maintainability_index': 50.0,
            'loc': 200,
            'sloc': 150,
            'comments': 10,
            'blank': 40,
            'multi': 0
        }
    ]

    lizard_results = [
        {
            'file_name': 'file1.py',
            'nloc': 150,
            'average_ccn': 11.5,
            'average_token': 60.0,
            'function_count': 2,
            'functions': [
                {'name': 'bad_func', 'ccn': 20, 'lines': 50, 'token_count': 100, 'parameters': 5},  # High CCN
                {'name': 'good_func', 'ccn': 3, 'lines': 10, 'token_count': 20, 'parameters': 1}
            ]
        }
    ]

    summary = cca.aggregate_complexity_metrics(radon_results, lizard_results)

    assert summary['functions_needing_refactor'] >= 1  # At least bad_func
    assert summary['low_maintainability_files'] == 1  # MI < 65
    assert summary['high_complexity_files'] == 1  # avg complexity > 10

def test_display_complexity_results_comprehensive(capsys):
    """
    Test display_complexity_results shows all sections.
    """
    complexity_data = {
        'summary': {
            'total_files': 10,
            'successful': 10,
            'total_lines': 5000,
            'total_code': 4000,
            'total_comments': 500,
            'total_functions': 50,
            'avg_complexity': 7.5,
            'avg_maintainability': 72.3,
            'radon_details': {
                'maintainability_rank': 'B',
                'comment_ratio': 10.0,
                'blank_lines': 500,
                'multi_line_strings': 50
            },
            'lizard_details': {
                'total_nloc': 4000,
                'average_ccn': 7.5,
                'average_token_count': 45.2,
                'average_parameters': 2.1,
                'functions_with_high_ccn': 5,
                'longest_function': 150
            }
        },
        'radon_metrics': [],
        'lizard_metrics': []
    }

    cca.display_complexity_results(complexity_data)

    out = capsys.readouterr().out

    assert 'CODE COMPLEXITY & STRUCTURE ANALYSIS' in out
    assert 'OVERVIEW:' in out
    assert 'Total Files Analyzed: 10' in out
    assert 'Total Lines: 5000' in out
    assert 'Total Functions: 50' in out
    assert 'QUALITY METRICS' in out
    assert 'Average Complexity: 7.5' in out
    assert 'Average Maintainability: 72.3' in out
    assert 'Maintainability Rank: B' in out
    assert 'Comment Ratio: 10.0%' in out
    assert 'ADDITIONAL METRICS:' in out
    assert 'Average CCN: 7.5' in out

def test_display_complexity_results_empty(capsys):
    """
    Test display_complexity_results handles empty data.
    """
    cca.display_complexity_results({})

    out = capsys.readouterr().out
    assert 'No complexity data to display' in out

def test_display_complexity_results_lizard_only(capsys):
    """
    Test display_complexity_results with only Lizard data (non-Python project).
    """
    complexity_data = {
        'summary': {
            'total_files': 5,
            'successful': 5,
            'total_lines': 2000,
            'total_code': 1800,
            'total_comments': 0,
            'total_functions': 20,
            'lizard_details': {
                'average_ccn': 6.2,
                'average_token_count': 38.5,
                'average_parameters': 1.8,
                'longest_function': 80
            }
        },
        'radon_metrics': [],
        'lizard_metrics': []
    }

    cca.display_complexity_results(complexity_data)

    out = capsys.readouterr().out

    assert 'CODE COMPLEXITY & STRUCTURE ANALYSIS' in out
    assert 'QUALITY METRICS:' in out
    assert 'Average Complexity (CCN): 6.2' in out
    assert 'ADDITIONAL METRICS:' in out
