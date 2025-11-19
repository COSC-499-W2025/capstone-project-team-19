"""
Basic detector function stubs.

Each detector should return:
    (hit: bool, evidence: list[dict])
"""


# OOP DETECTORS

def detect_classes(file_text: str, file_name: str):
    """Detect class definitions such as `class Foo:`."""
    return False, []


def detect_inheritance(file_text: str, file_name: str):
    """Detect class inheritance such as `class Foo(Bar):`."""
    return False, []


def detect_polymorphism(file_text: str, file_name: str):
    """Detect overridden methods or same method names across classes."""
    return False, []


# DATA STRUCTURE DETECTORS

def detect_hash_maps(file_text: str, file_name: str):
    """Detect usage of dict/hash-map patterns."""
    return False, []


def detect_sets(file_text: str, file_name: str):
    """Detect set literals, set() calls, or other set usage."""
    return False, []


def detect_queues_or_stacks(file_text: str, file_name: str):
    """
    Detect simple queue/stack usage (append/pop patterns or collections.deque).
    """
    return False, []


# ALGORITHM DETECTORS

def detect_recursion(file_text: str, file_name: str):
    """Detect recursive function calls."""
    return False, []


def detect_sorting_or_search(file_text: str, file_name: str):
    """Detect calls to `sort`, `sorted`, or binary search patterns."""
    return False, []


# CODE QUALITY DETECTORS

def detect_large_functions(file_text: str, file_name: str):
    """Detect very long functions that may indicate low-quality structure."""
    return False, []


def detect_comments_docstrings(file_text: str, file_name: str):
    """Detect comments or docstrings for clarity/documentation."""
    return False, []


def detect_duplicate_code(file_text: str, file_name: str):
    """Detect repeated code blocks (basic duplicate detection)."""
    return False, []


# STRUCTURE / SOFTWARE ENGINEERING

def detect_modular_design(file_text: str, file_name: str):
    """Detect evidence of modular design (imports, multiple modules)."""
    return False, []


def detect_test_files(file_text: str, file_name: str):
    """Detect pytest/unittest test cases or test file naming."""
    return False, []


def detect_ci_workflows(file_text: str, file_name: str):
    """Detect presence of CI/CD workflow configs (GitHub Actions)."""
    return False, []
