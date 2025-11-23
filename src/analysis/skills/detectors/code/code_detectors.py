"""
Basic detector function stubs.

Each detector should return:
    (hit: bool, evidence: list[dict])
"""

import re
from typing import Tuple, List, Dict


# OOP DETECTORS

def detect_classes(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect class definitions such as `class Foo:`."""
    pattern = r'\bclass\s+\w+'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_inheritance(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect class inheritance such as `class Foo(Bar):`."""
    # Matches: class Dog(Animal), class User extends Base, class Foo : public Bar
    pattern = r'class\s+\w+\s*[:(]'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_polymorphism(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect overridden methods or same method names across classes."""
    # Matches: @override, @Override, virtual void, abstract class
    pattern = r'(@override|@Override|virtual\s+\w+|abstract\s+class|abstract\s+def)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# DATA STRUCTURE DETECTORS

def detect_hash_maps(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect usage of dict/hash-map patterns."""
    # Matches: HashMap, dict(), Map<String>, map[], {"key": val}
    pattern = r'(HashMap|dict\(|Map<|map\[|\{\s*["\']?\w+["\']?\s*:)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_sets(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect set literals, set() calls, or other set usage."""
    # Matches: HashSet, set(), Set<String>, set =
    pattern = r'(HashSet|set\(|Set<|\bset\s*=)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_queues_or_stacks(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """
    Detect simple queue/stack usage (append/pop patterns or collections.deque).
    """
    # Matches: Queue, Stack, Deque, .push(), .pop(), .enqueue, .dequeue
    pattern = r'(Queue|Stack|Deque|\.push\(|\.pop\(|\.enqueue|\.dequeue)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# ALGORITHM DETECTORS

def detect_recursion(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect recursive function calls."""
    evidence = []
    lines = file_text.split('\n')

    # Find function definitions and track their names
    func_pattern = r'(def|function|func)\s+(\w+)\s*\('

    current_function = None
    function_start_line = 0

    for i, line in enumerate(lines, 1):
        # Check if this line defines a function
        match = re.search(func_pattern, line)
        if match:
            current_function = match.group(2)
            function_start_line = i

        # If we're inside a function, check if it calls itself
        if current_function:
            # Look for the function name followed by a parenthesis (function call)
            if re.search(rf'\b{current_function}\s*\(', line) and i != function_start_line:
                evidence.append({"file": file_name, "line": i})
                current_function = None  # Reset to avoid duplicate detections

    return (len(evidence) > 0, evidence)


def detect_sorting_or_search(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect calls to `sort`, `sorted`, or binary search patterns."""
    # Matches: .sort(), sorted(), Arrays.sort, Collections.sort, binary_search, binarySearch
    pattern = r'(\.sort\(|sorted\(|Arrays\.sort|Collections\.sort|binary.?search|linear.?search)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# CODE QUALITY DETECTORS

def detect_large_functions(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect very long functions that may indicate low-quality structure."""
    evidence = []
    lines = file_text.split('\n')

    # Pattern to detect function definitions
    func_pattern = r'^\s*(def|function|func|public|private|protected)\s+\w+\s*\('

    function_starts = []
    for i, line in enumerate(lines):
        if re.search(func_pattern, line):
            function_starts.append(i)

    # Check function lengths (threshold: 50 lines)
    for idx, start in enumerate(function_starts):
        if idx + 1 < len(function_starts):
            end = function_starts[idx + 1]
        else:
            end = len(lines)

        function_length = end - start
        if function_length > 50:
            evidence.append({"file": file_name, "line": start + 1})

    return (len(evidence) > 0, evidence)


def detect_comments_docstrings(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect comments or docstrings for clarity/documentation."""
    # Matches: #, //, /* */, """, ''', <!--
    pattern = r'(^\s*#|^\s*//|/\*|\"\"\"|\'\'\'|<!--)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_duplicate_code(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect repeated code blocks (basic duplicate detection)."""
    # Too complex for today - punt
    return False, []


# STRUCTURE / SOFTWARE ENGINEERING

def detect_modular_design(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect evidence of modular design (imports, multiple modules)."""
    # Matches: import, from X import, require(), #include
    pattern = r'(^import\s+|^from\s+.*\s+import|^require\(|^#include)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_test_files(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect pytest/unittest test cases or test file naming."""
    # Check filename patterns: test_, _test., spec., .test., __tests__, /tests/
    pattern = r'(test_|_test\.|spec\.|\.test\.|__tests__|/tests?/)'

    if re.search(pattern, file_name, re.IGNORECASE):
        return True, [{"file": file_name, "line": 0}]

    return False, []


def detect_ci_workflows(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect presence of CI/CD workflow configs (GitHub Actions)."""
    # Check filepath patterns: .github/workflows/, .gitlab-ci., Jenkinsfile, .circleci/, .travis.yml
    pattern = r'(\.github/workflows/|\.gitlab-ci\.|Jenkinsfile|\.circleci/|\.travis\.yml)'

    if re.search(pattern, file_name):
        return True, [{"file": file_name, "line": 0}]

    return False, []
