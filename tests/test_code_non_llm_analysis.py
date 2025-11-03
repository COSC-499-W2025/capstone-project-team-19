"""
Test suite for code_non_llm_analysis.py

Tests the orchestration of non-LLM code analysis which combines:
- Code complexity analysis (via code_complexity_analyzer)
- Git individual project analysis (via git_individual_analyzer)
"""

import pytest
from unittest.mock import MagicMock
import src.code_non_llm_analysis as cnlla


def test_run_code_non_llm_analysis_both_successful(tmp_sqlite_conn, monkeypatch, capsys):
    """
    Test happy path when both complexity and git analysis succeed.
    Should display results from both analyzers.
    """
    # Mock complexity analysis
    mock_complexity_data = {
        'summary': {
            'total_files': 5,
            'successful': 5,
            'total_lines': 1000,
            'avg_complexity': 5.2,
            'avg_maintainability': 75.5
        },
        'radon_metrics': [],
        'lizard_metrics': []
    }

    # Mock git analysis
    mock_git_data = {
        'has_git': True,
        'repo_path': '/fake/path',
        'commit_stats': {
            'total_commits': 50,
            'first_commit_date': '2024-01-01',
            'last_commit_date': '2024-06-01',
            'time_span_days': 150,
            'average_commits_per_week': 2.3,
            'average_commits_per_month': 10.0
        },
        'timeline_data': [],
        'weekly_changes': {},
        'activity_timeline': {}
    }

    # Patch the analyzer functions
    monkeypatch.setattr(cnlla, 'analyze_code_complexity', lambda conn, user_id, pn, zp: mock_complexity_data)
    monkeypatch.setattr(cnlla, 'analyze_git_individual_project', lambda conn, user_id, pn, zp: mock_git_data)

    # Mock display functions to verify they're called
    display_complexity_called = False
    display_git_called = False

    def mock_display_complexity(data):
        nonlocal display_complexity_called
        display_complexity_called = True
        assert data == mock_complexity_data

    def mock_display_git(data):
        nonlocal display_git_called
        display_git_called = True
        assert data == mock_git_data

    monkeypatch.setattr(cnlla, 'display_complexity_results', mock_display_complexity)
    monkeypatch.setattr(cnlla, 'display_git_results', mock_display_git)

    # Run the analysis
    cnlla.run_code_non_llm_analysis(tmp_sqlite_conn, 1, 'test_project', '/path/to/test.zip')

    # Verify both display functions were called
    assert display_complexity_called, "Complexity results should be displayed"
    assert display_git_called, "Git results should be displayed"


def test_run_code_non_llm_analysis_no_complexity_data(tmp_sqlite_conn, monkeypatch, capsys):
    """
    Test when complexity analysis returns None/empty.
    Should skip complexity display but continue with git analysis.
    """
    mock_git_data = {
        'has_git': True,
        'commit_stats': {'total_commits': 10}
    }

    monkeypatch.setattr(cnlla, 'analyze_code_complexity', lambda conn, user_id, pn, zp: None)
    monkeypatch.setattr(cnlla, 'analyze_git_individual_project', lambda conn, user_id, pn, zp: mock_git_data)

    display_complexity_called = False
    display_git_called = False

    def mock_display_complexity(data):
        nonlocal display_complexity_called
        display_complexity_called = True

    def mock_display_git(data):
        nonlocal display_git_called
        display_git_called = True

    monkeypatch.setattr(cnlla, 'display_complexity_results', mock_display_complexity)
    monkeypatch.setattr(cnlla, 'display_git_results', mock_display_git)

    cnlla.run_code_non_llm_analysis(tmp_sqlite_conn, 1, 'test_project', '/path/to/test.zip')

    # Complexity display should not be called
    assert not display_complexity_called, "Should not display empty complexity results"
    # Git display should still be called
    assert display_git_called, "Should still display git results"


def test_run_code_non_llm_analysis_no_git_repo(tmp_sqlite_conn, monkeypatch, capsys):
    """
    Test when no git repository is found (has_git=False).
    Should not display git results.
    """
    mock_complexity_data = {
        'summary': {'total_files': 3}
    }

    mock_git_data = {
        'has_git': False
    }

    monkeypatch.setattr(cnlla, 'analyze_code_complexity', lambda conn, user_id, pn, zp: mock_complexity_data)
    monkeypatch.setattr(cnlla, 'analyze_git_individual_project', lambda conn, user_id, pn, zp: mock_git_data)

    display_git_called = False

    def mock_display_git(data):
        nonlocal display_git_called
        display_git_called = True

    monkeypatch.setattr(cnlla, 'display_complexity_results', lambda data: None)
    monkeypatch.setattr(cnlla, 'display_git_results', mock_display_git)

    cnlla.run_code_non_llm_analysis(tmp_sqlite_conn, 1, 'test_project', '/path/to/test.zip')

    # Git display should not be called when no git repo
    assert not display_git_called, "Should not display git results when no git repo found"

def test_run_code_non_llm_analysis_both_empty(tmp_sqlite_conn, monkeypatch, capsys):
    """
    Test when both analyzers return empty/None.
    Should handle gracefully without crashing.
    """
    monkeypatch.setattr(cnlla, 'analyze_code_complexity', lambda conn, user_id, pn, zp: None)
    monkeypatch.setattr(cnlla, 'analyze_git_individual_project', lambda conn, user_id, pn, zp: None)

    display_complexity_called = False
    display_git_called = False

    def mock_display_complexity(data):
        nonlocal display_complexity_called
        display_complexity_called = True

    def mock_display_git(data):
        nonlocal display_git_called
        display_git_called = True

    monkeypatch.setattr(cnlla, 'display_complexity_results', mock_display_complexity)
    monkeypatch.setattr(cnlla, 'display_git_results', mock_display_git)

    # Should not raise an exception
    cnlla.run_code_non_llm_analysis(tmp_sqlite_conn, 1, 'test_project', '/path/to/test.zip')

    # Neither display should be called
    assert not display_complexity_called
    assert not display_git_called


def test_run_code_non_llm_analysis_passes_correct_params(tmp_sqlite_conn, monkeypatch):
    """
    Test that parameters are passed correctly to both analyzer functions.
    """
    complexity_params = None
    git_params = None

    def mock_analyze_complexity(conn, user_id, project_name, zip_path):
        nonlocal complexity_params
        complexity_params = (conn, user_id, project_name, zip_path)
        return {'summary': {'total_files': 1}}

    def mock_analyze_git(conn, user_id, project_name, zip_path):
        nonlocal git_params
        git_params = (conn, user_id, project_name, zip_path)
        return {'has_git': True}

    monkeypatch.setattr(cnlla, 'analyze_code_complexity', mock_analyze_complexity)
    monkeypatch.setattr(cnlla, 'analyze_git_individual_project', mock_analyze_git)
    monkeypatch.setattr(cnlla, 'display_complexity_results', lambda data: None)
    monkeypatch.setattr(cnlla, 'display_git_results', lambda data: None)

    test_conn = tmp_sqlite_conn
    test_user_id = 42
    test_project = 'my_project'
    test_zip = '/path/to/my_project.zip'

    cnlla.run_code_non_llm_analysis(test_conn, test_user_id, test_project, test_zip)

    # Verify complexity analyzer received correct params
    assert complexity_params is not None
    assert complexity_params[0] == test_conn
    assert complexity_params[1] == test_user_id
    assert complexity_params[2] == test_project
    assert complexity_params[3] == test_zip

    # Verify git analyzer received correct params
    assert git_params is not None
    assert git_params[0] == test_conn
    assert git_params[1] == test_user_id
    assert git_params[2] == test_project
    assert git_params[3] == test_zip
