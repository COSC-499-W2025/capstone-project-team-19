import os
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
import subprocess
import src.analysis.code_individual.git_individual_analyzer as gia


# Helper to create subprocess result
def make_subprocess_result(stdout="", stderr="", returncode=0):
    """Create a mock subprocess.CompletedProcess result."""
    result = Mock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


def test_analyze_git_individual_project_with_repo(tmp_sqlite_conn, tmp_path, monkeypatch, capsys):
    """
    Test happy path: local git repository found and analyzed successfully.
    """
    # Create fake git directory
    fake_repo = tmp_path / "fake_project" / ".git"
    fake_repo.mkdir(parents=True)

    # Mock bfs_find_repo to return our fake repo
    monkeypatch.setattr(gia, 'bfs_find_repo', lambda base, max_depth: str(fake_repo.parent))

    # Mock get_commit_statistics
    mock_commit_stats = {
        'total_commits': 50,
        'first_commit_date': '2024-01-01 10:00:00 -0500',
        'last_commit_date': '2024-06-01 10:00:00 -0500',
        'time_span_days': 150,
        'average_commits_per_week': 2.3,
        'average_commits_per_month': 10.0,
        'unique_authors': 1,
        'recent_commits': [
            {'date': '2024-06-01 10:00:00', 'message': 'Latest commit'}
        ]
    }
    monkeypatch.setattr(gia, 'get_commit_statistics', lambda repo_path: mock_commit_stats)

    # Mock get_lines_timeline
    mock_timeline = [
        {'commit_hash': 'abc1234', 'date': '2024-01-01', 'timestamp': 1704067200,
         'lines_added': 100, 'lines_deleted': 20, 'net_lines': 80}
    ]
    monkeypatch.setattr(gia, 'get_lines_timeline', lambda repo_path: mock_timeline)

    # Mock calculate_weekly_changes
    mock_weekly = {
        'weeks': ['2024-01-01'],
        'additions_per_week': [100],
        'deletions_per_week': [20],
        'net_per_week': [80],
        'total_weeks': 1
    }
    monkeypatch.setattr(gia, 'calculate_weekly_changes', lambda timeline: mock_weekly)

    # Mock generate_activity_timeline
    mock_activity = {
        'commits_per_day': {'2024-01-01': 1},
        'commits_per_month': {'2024-01': 1},
        'busiest_day': {'date': '2024-01-01', 'commits': 1},
        'busiest_month': {'month': '2024-01', 'commits': 1},
        'total_active_days': 1,
        'total_active_months': 1,
        'average_commits_per_active_day': 1.0
    }
    monkeypatch.setattr(gia, 'generate_activity_timeline', lambda timeline: mock_activity)

    # Run analysis
    result = gia.analyze_git_individual_project(
        tmp_sqlite_conn, 1, 'test_project', str(tmp_path / 'test.zip')
    )

    # Verify result structure
    assert result is not None
    assert result['has_git'] is True
    assert result['repo_path'] == str(fake_repo.parent)
    assert result['commit_stats'] == mock_commit_stats
    assert result['timeline_data'] == mock_timeline
    assert result['weekly_changes'] == mock_weekly
    assert result['activity_timeline'] == mock_activity

    # Verify output contains project name
    out = capsys.readouterr().out
    assert 'test_project' in out
    assert 'Analyzing Git Repository' in out

def test_get_commit_statistics_success(tmp_path, monkeypatch):
    """
    Test get_commit_statistics with successful git commands.
    """
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    # Mock subprocess.run for different git commands
    def mock_subprocess_run(cmd, **kwargs):
        if 'rev-list' in cmd:
            # Total commit count
            return make_subprocess_result(stdout="50\n")
        elif 'log' in cmd and '--reverse' in cmd:
            # First commit date
            return make_subprocess_result(stdout="2024-01-01 10:00:00 -0500\n2024-01-02 11:00:00 -0500\n")
        elif 'log' in cmd and '--max-count=1' in cmd and '%ai' in ' '.join(cmd):
            # Last commit date
            return make_subprocess_result(stdout="2024-06-01 10:00:00 -0500\n")
        elif 'log' in cmd and '%an' in ' '.join(cmd):
            # Authors
            return make_subprocess_result(stdout="Author1\nAuthor2\nAuthor1\n")
        elif 'log' in cmd and '%ai|%s' in ' '.join(cmd):
            # Commit messages
            return make_subprocess_result(stdout="2024-06-01 10:00:00 -0500|Latest commit\n2024-05-30 09:00:00 -0500|Previous commit\n")
        return make_subprocess_result()

    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run)

    result = gia.get_commit_statistics(str(fake_repo))

    assert result['total_commits'] == 50
    assert result['first_commit_date'] == '2024-01-01 10:00:00 -0500'
    assert result['last_commit_date'] == '2024-06-01 10:00:00 -0500'
    assert result['time_span_days'] == 152 
    assert result['average_commits_per_week'] > 0
    assert result['average_commits_per_month'] > 0
    assert result['unique_authors'] == 2
    assert len(result['recent_commits']) == 2
    assert result['recent_commits'][0]['message'] == 'Latest commit'


def test_get_commit_statistics_no_commits(tmp_path, monkeypatch, capsys):
    """
    Test get_commit_statistics when repository has no commits.
    Function should handle empty output gracefully and return empty dict.
    """
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    def mock_subprocess_run(cmd, **kwargs):
        # Simulate empty repository - this causes int('') to fail
        return make_subprocess_result(stdout="", returncode=0)

    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run)

    result = gia.get_commit_statistics(str(fake_repo))

    # Function returns empty dict on error (including int('') error)
    assert result == {}

    # Should print an error message
    out = capsys.readouterr().out
    assert 'Error getting commit statistics' in out

def test_get_commit_statistics_error_handling(tmp_path, monkeypatch):
    """
    Test get_commit_statistics handles subprocess errors gracefully.
    """
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    def mock_subprocess_run(cmd, **kwargs):
        # Simulate git command failure
        return make_subprocess_result(stdout="", stderr="fatal: not a git repository", returncode=128)

    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run)

    result = gia.get_commit_statistics(str(fake_repo))
    assert result['total_commits'] == 0
    assert result['unique_authors'] == 0

def test_get_lines_timeline_success(tmp_path, monkeypatch):
    """
    Test get_lines_timeline with successful parsing.
    """
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    # Mock git log --numstat output
    git_output = """abc1234|2024-01-01 10:00:00 -0500
10\t5\tfile1.py
20\t3\tfile2.py

def5678|2024-01-02 11:00:00 -0500
15\t2\tfile3.py
"""

    def mock_subprocess_run(cmd, **kwargs):
        return make_subprocess_result(stdout=git_output)

    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run)

    result = gia.get_lines_timeline(str(fake_repo))

    assert len(result) == 2
    assert result[0]['commit_hash'] == 'abc1234'
    assert result[0]['lines_added'] == 30  # 10 + 20
    assert result[0]['lines_deleted'] == 8  # 5 + 3
    assert result[0]['net_lines'] == 22  # 30 - 8
    assert result[1]['commit_hash'] == 'def5678'
    assert result[1]['lines_added'] == 15
    assert result[1]['lines_deleted'] == 2


def test_get_lines_timeline_binary_files(tmp_path, monkeypatch):
    """
    Test get_lines_timeline handles binary files (non-digit additions/deletions).
    """
    fake_repo = tmp_path / "repo"
    fake_repo.mkdir()

    # Binary files show as '-' instead of numbers
    git_output = """abc1234|2024-01-01 10:00:00 -0500
-\t-\tbinary.png
10\t5\tfile1.py
"""

    def mock_subprocess_run(cmd, **kwargs):
        return make_subprocess_result(stdout=git_output)

    monkeypatch.setattr(subprocess, 'run', mock_subprocess_run)

    result = gia.get_lines_timeline(str(fake_repo))

    assert len(result) == 1
    assert result[0]['lines_added'] == 10  # Only counts file1.py
    assert result[0]['lines_deleted'] == 5


def test_calculate_weekly_changes_success(monkeypatch):
    """
    Test calculate_weekly_changes aggregates timeline data correctly.
    """
    import pandas as pd

    # Timeline with commits across multiple weeks
    timeline_data = [
        {'timestamp': 1704067200, 'lines_added': 100, 'lines_deleted': 20, 'net_lines': 80},  # Week 1
        {'timestamp': 1704153600, 'lines_added': 50, 'lines_deleted': 10, 'net_lines': 40},   # Week 1
        {'timestamp': 1704672000, 'lines_added': 30, 'lines_deleted': 5, 'net_lines': 25},    # Week 2
    ]

    result = gia.calculate_weekly_changes(timeline_data)

    assert 'weeks' in result
    assert 'additions_per_week' in result
    assert 'deletions_per_week' in result
    assert 'net_per_week' in result
    assert 'total_weeks' in result
    assert result['total_weeks'] >= 1


def test_calculate_weekly_changes_empty_timeline():
    """
    Test calculate_weekly_changes handles empty timeline.
    """
    result = gia.calculate_weekly_changes([])
    assert result == {}


def test_generate_activity_timeline_success():
    """
    Test generate_activity_timeline creates correct activity patterns.
    """
    timeline_data = [
        {'timestamp': 1704067200, 'commit_hash': 'a1'},  # 2024-01-01
        {'timestamp': 1704067200, 'commit_hash': 'a2'},  # 2024-01-01 (same day)
        {'timestamp': 1704153600, 'commit_hash': 'a3'},  # 2024-01-02
    ]

    result = gia.generate_activity_timeline(timeline_data)

    assert 'commits_per_day' in result
    assert 'commits_per_month' in result
    assert 'busiest_day' in result
    assert 'busiest_month' in result
    assert 'total_active_days' in result
    assert 'total_active_months' in result
    assert 'average_commits_per_active_day' in result

    # Should detect that 2024-01-01 is the busiest day (2 commits)
    assert result['busiest_day']['commits'] == 2
    assert result['total_active_days'] == 2


def test_generate_activity_timeline_empty():
    """
    Test generate_activity_timeline handles empty timeline.
    """
    result = gia.generate_activity_timeline([])
    assert result == {}


def test_display_git_results_comprehensive(capsys):
    """
    Test display_git_results shows all sections when data is available.
    """
    git_data = {
        'has_git': True,
        'commit_stats': {
            'total_commits': 50,
            'time_span_days': 150,
            'first_commit_date': '2024-01-01 10:00:00 -0500',
            'last_commit_date': '2024-06-01 10:00:00 -0500',
            'average_commits_per_week': 2.3,
            'average_commits_per_month': 10.0,
            'recent_commits': [
                {'date': '2024-06-01 10:00:00 -0500', 'message': 'Latest commit'},
                {'date': '2024-05-30 09:00:00 -0500', 'message': 'Previous commit'}
            ]
        },
        'weekly_changes': {
            'weeks': ['2024-01-01', '2024-01-08'],
            'additions_per_week': [100, 50],
            'deletions_per_week': [20, 10],
            'net_per_week': [80, 40],
            'total_weeks': 2
        },
        'activity_timeline': {
            'total_active_days': 10,
            'total_active_months': 2,
            'average_commits_per_active_day': 5.0,
            'busiest_day': {'date': '2024-01-15', 'commits': 8},
            'busiest_month': {'month': '2024-01', 'commits': 30}
        }
    }

    gia.display_git_results(git_data)

    out = capsys.readouterr().out

    # Check all major sections are displayed
    assert 'GIT REPOSITORY ANALYSIS' in out
    assert 'OVERVIEW:' in out
    assert 'Total Commits: 50' in out
    assert 'Time Span: 150 days' in out
    assert 'COMMIT FREQUENCY:' in out
    assert 'Average per Week: 2.3' in out
    assert 'CODE CHANGE SUMMARY:' in out
    assert 'Total Weeks Active: 2' in out
    assert 'ACTIVITY PATTERNS:' in out
    assert 'Total Active Days: 10' in out
    assert 'RECENT COMMITS:' in out
    assert 'Latest commit' in out

def test_display_git_results_minimal_data(capsys):
    """
    Test display_git_results handles minimal data gracefully.
    """
    git_data = {
        'has_git': True,
        'commit_stats': {},
        'weekly_changes': {},
        'activity_timeline': {}
    }

    gia.display_git_results(git_data)

    out = capsys.readouterr().out
    assert 'GIT REPOSITORY ANALYSIS' in out
    # Should not crash even with empty data
