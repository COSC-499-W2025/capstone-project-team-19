"""
Unit tests for code detector functions.

Tests each detector with positive and negative cases to ensure correct pattern matching.
"""

import pytest
from src.analysis.skills.detectors.code.code_detectors import (
    detect_classes,
    detect_inheritance,
    detect_polymorphism,
    detect_hash_maps,
    detect_sets,
    detect_queues_or_stacks,
    detect_recursion,
    detect_sorting_or_search,
    detect_large_functions,
    detect_comments_docstrings,
    detect_duplicate_code,
    detect_modular_design,
    detect_test_files,
    detect_ci_workflows,
)


# OOP DETECTORS

def test_detect_classes_positive():
    """Test that classes are detected."""
    code = """
class User:
    pass

class Admin:
    pass
"""
    hit, evidence = detect_classes(code, "test.py")
    assert hit is True
    assert len(evidence) == 2
    assert evidence[0]["file"] == "test.py"
    assert evidence[0]["line"] == 2


def test_detect_classes_negative():
    """Test that non-class code doesn't trigger detection."""
    code = "def function(): pass"
    hit, evidence = detect_classes(code, "test.py")
    assert hit is False
    assert len(evidence) == 0


def test_detect_inheritance_positive():
    """Test that inheritance is detected."""
    code = """
class Dog(Animal):
    pass

class User extends BaseUser:
    pass
"""
    hit, evidence = detect_inheritance(code, "test.py")
    assert hit is True
    assert len(evidence) >= 1


def test_detect_inheritance_negative():
    """Test that simple classes without inheritance don't trigger."""
    code = "class Simple:\n    pass"
    hit, evidence = detect_inheritance(code, "test.py")
    assert hit is False


def test_detect_polymorphism_positive():
    """Test that polymorphism patterns are detected."""
    code = """
@override
def method(self):
    pass

virtual void process() {}

abstract class Shape {}
"""
    hit, evidence = detect_polymorphism(code, "test.py")
    assert hit is True
    assert len(evidence) >= 2


def test_detect_polymorphism_negative():
    """Test that regular code doesn't trigger polymorphism."""
    code = "def regular_function(): pass"
    hit, evidence = detect_polymorphism(code, "test.py")
    assert hit is False


# DATA STRUCTURE DETECTORS

def test_detect_hash_maps_positive():
    """Test that hash map usage is detected."""
    code = """
user_data = dict()
map = HashMap<String, Integer>()
config = {"key": "value"}
"""
    hit, evidence = detect_hash_maps(code, "test.py")
    assert hit is True
    assert len(evidence) >= 2


def test_detect_hash_maps_negative():
    """Test that non-map code doesn't trigger."""
    code = "x = 5"
    hit, evidence = detect_hash_maps(code, "test.py")
    assert hit is False


def test_detect_sets_positive():
    """Test that set usage is detected."""
    code = """
unique = set()
numbers = HashSet<Integer>()
items = set([1, 2, 3])
"""
    hit, evidence = detect_sets(code, "test.py")
    assert hit is True
    assert len(evidence) >= 2


def test_detect_sets_negative():
    """Test that non-set code doesn't trigger."""
    code = "x = [1, 2, 3]"
    hit, evidence = detect_sets(code, "test.py")
    assert hit is False


def test_detect_queues_or_stacks_positive():
    """Test that queue/stack usage is detected."""
    code = """
stack = Stack()
queue = Queue()
stack.push(item)
queue.pop()
"""
    hit, evidence = detect_queues_or_stacks(code, "test.py")
    assert hit is True
    assert len(evidence) >= 3


def test_detect_queues_or_stacks_negative():
    """Test that non-queue/stack code doesn't trigger."""
    code = "x = [1, 2, 3]"
    hit, evidence = detect_queues_or_stacks(code, "test.py")
    assert hit is False


# ALGORITHM DETECTORS

def test_detect_recursion_positive():
    """Test that recursive functions are detected."""
    code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)
"""
    hit, evidence = detect_recursion(code, "test.py")
    assert hit is True
    assert len(evidence) >= 1


def test_detect_recursion_negative():
    """Test that non-recursive functions don't trigger."""
    code = """
def simple(n):
    return n + 1
"""
    hit, evidence = detect_recursion(code, "test.py")
    assert hit is False


def test_detect_sorting_or_search_positive():
    """Test that sorting and search algorithms are detected."""
    code = """
data.sort()
result = sorted(items)
index = binary_search(arr, target)
"""
    hit, evidence = detect_sorting_or_search(code, "test.py")
    assert hit is True
    assert len(evidence) >= 3


def test_detect_sorting_or_search_negative():
    """Test that non-algorithm code doesn't trigger."""
    code = "x = [1, 2, 3]"
    hit, evidence = detect_sorting_or_search(code, "test.py")
    assert hit is False


# CODE QUALITY DETECTORS

def test_detect_large_functions_positive():
    """Test that large functions are detected."""
    # Create a function with more than 50 lines
    lines = ["def large_function():\n"]
    lines.extend(["    x = 1\n"] * 60)
    code = "".join(lines)

    hit, evidence = detect_large_functions(code, "test.py")
    assert hit is True
    assert len(evidence) >= 1


def test_detect_large_functions_negative():
    """Test that small functions don't trigger."""
    code = """
def small():
    return 1
"""
    hit, evidence = detect_large_functions(code, "test.py")
    assert hit is False


def test_detect_comments_docstrings_positive():
    """Test that comments and docstrings are detected."""
    code = """
# This is a comment
def foo():
    \"\"\"This is a docstring\"\"\"
    // Another comment
    pass
"""
    hit, evidence = detect_comments_docstrings(code, "test.py")
    assert hit is True
    assert len(evidence) >= 2


def test_detect_comments_docstrings_negative():
    """Test that code without comments doesn't trigger."""
    code = "x = 5"
    hit, evidence = detect_comments_docstrings(code, "test.py")
    assert hit is False


def test_detect_duplicate_code():
    """Test that duplicate code detector is stubbed out."""
    code = "anything"
    hit, evidence = detect_duplicate_code(code, "test.py")
    assert hit is False
    assert len(evidence) == 0


# STRUCTURE DETECTORS

def test_detect_modular_design_positive():
    """Test that imports are detected."""
    code = """
import os
from typing import List
require('express')
#include <stdio.h>
"""
    hit, evidence = detect_modular_design(code, "test.py")
    assert hit is True
    assert len(evidence) >= 2


def test_detect_modular_design_negative():
    """Test that code without imports doesn't trigger."""
    code = "x = 5"
    hit, evidence = detect_modular_design(code, "test.py")
    assert hit is False


def test_detect_test_files_positive():
    """Test that test file names are detected."""
    test_cases = [
        "test_user.py",
        "user_test.py",
        "user.test.js",
        "user.spec.ts",
        "src/tests/helper.py",
        "__tests__/component.js"
    ]

    for filename in test_cases:
        hit, evidence = detect_test_files("", filename)
        assert hit is True, f"Should detect {filename} as test file"


def test_detect_test_files_negative():
    """Test that non-test files don't trigger."""
    non_test_files = [
        "main.py",
        "user.py",
        "component.js"
    ]

    for filename in non_test_files:
        hit, evidence = detect_test_files("", filename)
        assert hit is False, f"Should not detect {filename} as test file"


def test_detect_ci_workflows_positive():
    """Test that CI/CD files are detected."""
    ci_files = [
        ".github/workflows/test.yml",
        ".gitlab-ci.yml",
        "Jenkinsfile",
        ".circleci/config.yml",
        ".travis.yml"
    ]

    for filename in ci_files:
        hit, evidence = detect_ci_workflows("", filename)
        assert hit is True, f"Should detect {filename} as CI file"


def test_detect_ci_workflows_negative():
    """Test that non-CI files don't trigger."""
    non_ci_files = [
        "main.py",
        "config.yml",
        "workflow.txt"
    ]

    for filename in non_ci_files:
        hit, evidence = detect_ci_workflows("", filename)
        assert hit is False, f"Should not detect {filename} as CI file"


# EDGE CASES

def test_detectors_handle_empty_input():
    """Test that all detectors handle empty input gracefully."""
    detectors = [
        detect_classes,
        detect_inheritance,
        detect_polymorphism,
        detect_hash_maps,
        detect_sets,
        detect_queues_or_stacks,
        detect_recursion,
        detect_sorting_or_search,
        detect_large_functions,
        detect_comments_docstrings,
        detect_duplicate_code,
        detect_modular_design,
    ]

    for detector in detectors:
        hit, evidence = detector("", "empty.py")
        assert hit is False
        assert evidence == []


def test_evidence_format():
    """Test that evidence has correct format."""
    code = "class Test: pass"
    hit, evidence = detect_classes(code, "test.py")

    assert hit is True
    assert len(evidence) > 0

    # Check evidence structure
    for item in evidence:
        assert "file" in item
        assert "line" in item
        assert item["file"] == "test.py"
        assert isinstance(item["line"], int)
        assert item["line"] > 0
