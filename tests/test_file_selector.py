"""
Tests for file_selector module.
Covers main user interaction paths with mocked inputs.
"""
import pytest
from src.google_drive_auth.file_selector import (
    select_from_matches,
    handle_no_matches,
    search_and_select,
    browse_all_files,
)

pytestmark = pytest.mark.no_shared_db


def test_select_from_matches_valid_and_invalid(monkeypatch):
    """Covers valid, invalid, and out-of-range selections."""
    maybe_matches = [
        ('id1', 'Doc1.pdf', 'application/pdf'),
        ('id2', 'Doc2.pdf', 'application/pdf'),
    ]
    all_files = maybe_matches
    search_func = lambda term, files: []
    # invalid → out of range → valid
    inputs = iter(['abc', '99', '2'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))

    result = select_from_matches('test.txt', maybe_matches, all_files, search_func)
    assert result == ('id2', 'Doc2.pdf', 'application/pdf')


def test_handle_no_matches_all_options(monkeypatch):
    """Covers browse, search, and skip branches."""
    all_files = [
        ('id1', 'File1.txt', 'text/plain'),
        ('id2', 'File2.txt', 'text/plain'),
    ]

    def mock_search(term, files):
        return [('id2', 'File2.txt', 'text/plain')] if '2' in term else []

    # user: browse (b) → select 1
    inputs = iter(['b', '1'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert handle_no_matches('test.txt', all_files, mock_search) == ('id1', 'File1.txt', 'text/plain')

    # user: search for "2" → select 1
    inputs = iter(['2', '1'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert handle_no_matches('test.txt', all_files, mock_search) == ('id2', 'File2.txt', 'text/plain')

    # user: skip
    monkeypatch.setattr('builtins.input', lambda _: 's')
    assert handle_no_matches('test.txt', all_files, mock_search) is None


def test_search_and_select_found_and_not_found(monkeypatch):
    """Tests both found and not-found search flows."""
    all_files = [('id1', 'Doc1.pdf', 'application/pdf')]

    def mock_search(term, files):
        return all_files if 'Doc' in term else []

    # Case 1: found → user selects 1
    monkeypatch.setattr('builtins.input', lambda _: '1')
    assert search_and_select('Doc', all_files, mock_search, 'test.txt') == ('id1', 'Doc1.pdf', 'application/pdf')

    # Case 2: not found → returns None
    assert search_and_select('Nope', all_files, mock_search, 'test.txt') is None


def test_browse_all_files_basic_and_paginated(monkeypatch):
    """Covers browsing one-page and paginated file lists."""
    # One-page: 3 files, user selects 2
    all_files = [('id1', 'A.txt', ''), ('id2', 'B.txt', ''), ('id3', 'C.txt', '')]
    monkeypatch.setattr('builtins.input', lambda _: '2')
    assert browse_all_files('test.txt', all_files) == ('id2', 'B.txt', '')

    # Multi-page: go to next page, then select 1
    files_25 = [('id' + str(i), f'File{i}.txt', '') for i in range(1, 25)]
    inputs = iter(['21', '1'])
    monkeypatch.setattr('builtins.input', lambda _: next(inputs))
    assert browse_all_files('test.txt', files_25) == ('id21', 'File21.txt', '')


def test_edge_cases(monkeypatch):
    """Covers empty lists and skip/invalid handling."""
    # Empty browse list
    monkeypatch.setattr('builtins.input', lambda _: '1')
    assert browse_all_files('test.txt', []) is None

    # Empty search results
    monkeypatch.setattr('builtins.input', lambda _: '2')
    assert select_from_matches('test.txt', [], [], lambda t, f: []) is None
