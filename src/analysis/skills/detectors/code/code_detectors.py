"""
Basic detector function stubs.

Each detector should return:
    (hit: bool, evidence: list[dict])
"""

import re
from typing import Tuple, List, Dict


# HELPER FUNCTIONS

def _is_comment_line(line: str) -> bool:
    """Check if a line is a comment."""
    stripped = line.strip()
    return stripped.startswith('#') or stripped.startswith('//') or stripped.startswith('*')


def _is_likely_in_string(line: str, pattern_match_pos: int) -> bool:
    """Simple heuristic: check if match position is inside quotes."""
    # Count quotes before the match position
    before_match = line[:pattern_match_pos]
    single_quotes = before_match.count("'")
    double_quotes = before_match.count('"')

    # If odd number of quotes, we're likely inside a string
    return (single_quotes % 2 == 1) or (double_quotes % 2 == 1)


# OOP DETECTORS

def detect_classes(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect class definitions such as `class Foo:`."""
    # Must be at start of line (possibly after whitespace) to avoid strings/comments
    pattern = r'^\s*class\s+\w+'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_inheritance(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect class inheritance such as `class Foo(Bar):`."""
    # Matches: class Dog(Animal), class User extends Base, class Foo : public Bar
    # Must have something in parentheses or 'extends' keyword
    # Must be at start of line to avoid strings
    pattern = r'^\s*(class\s+\w+\s*\([^)]+\)|class\s+\w+\s+extends\s+\w+|class\s+\w+\s*:\s*(public|private|protected))'
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
    # Avoid matching inside strings by requiring word boundaries and not being preceded by quotes
    pattern = r'(\bHashMap\b|=\s*dict\(|=\s*\{|Map<|\bmap\[)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        # Skip lines that are comments
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
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
    pattern = r'(\.sort\(|\bsorted\(|Arrays\.sort|Collections\.sort|binary.?search|linear.?search)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
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


# TESTING DETECTORS

def detect_assertions(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect test assertions."""
    # Matches: assert, expect, should, chai.
    pattern = r'(\bassert\b|expect\(|should\.|chai\.)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_mocking_or_fixtures(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect mocking or fixture usage in tests."""
    # Matches: mock, Mock, @patch, fixture, stub
    pattern = r'(mock|Mock|@patch|@fixture|stub|@pytest\.fixture)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# ERROR HANDLING & SECURITY

def detect_error_handling(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect error handling patterns."""
    # Matches: try:, except, catch, throw, raises
    # Must be at start of line or after whitespace for try/except
    pattern = r'(^\s*try:|^\s*except\b|catch\s*\(|throw\s+new|raises\()'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_input_validation(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect input validation patterns."""
    # Matches: validate, validator, sanitize, schema.validate
    pattern = r'(\bvalidate\(|validator|sanitize\(|schema\.validate|\.is_valid\()'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_env_variable_usage(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect environment variable usage."""
    # Matches: process.env, os.environ, getenv, .env (but not "environment" variable)
    pattern = r'(process\.env|os\.environ|\bgetenv\(|import dotenv|load_dotenv)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_crypto_usage(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect cryptography and security library usage."""
    # Matches: hashlib, bcrypt, crypto imports/usage, encrypt/decrypt functions
    pattern = r'(import hashlib|import bcrypt|crypto\.|encrypt\(|decrypt\(|jwt\.|hashlib\.|bcrypt\.)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# ARCHITECTURE DETECTORS

def detect_mvc_folders(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect MVC folder structure."""
    # Check filepath for models, views, controllers folders
    pattern = r'/(models|views|controllers)/'

    if re.search(pattern, file_name, re.IGNORECASE):
        return True, [{"file": file_name, "line": 0}]

    return False, []


def detect_api_routes(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect API route definitions."""
    # Matches: @app.route, @router., app.get(, @GetMapping, @PostMapping
    # Must be at start of line (decorator) or actual function call
    pattern = r'(^\s*@app\.route|^\s*@router\.|^\s*@(Get|Post|Put|Delete)Mapping|app\.(get|post|put|delete)\()'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# FRONTEND DETECTORS

def detect_components(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect frontend component usage."""
    # Matches: React.Component, extends Component, Vue.component, @Component
    pattern = r'(React\.Component|class \w+ extends Component|Vue\.component|^\s*@Component|createComponent)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


# BACKEND DETECTORS

def detect_serialization(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect data serialization patterns."""
    # Matches: JSON.stringify, json.dumps, serialize, toJSON, JsonSerializer
    pattern = r'(JSON\.stringify|json\.dumps|\bserialize\(|\.toJSON\(|JsonSerializer|pickle\.dump)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_database_queries(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect database query usage."""
    # Matches: SELECT, INSERT, UPDATE, cursor.execute, query(, findOne
    # For SQL keywords, require word boundaries or start of string
    pattern = r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|cursor\.execute|\.query\(|\.findOne|\.findMany|\.find\(|\.save\()'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)


def detect_caching(file_text: str, file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect caching implementation."""
    # Matches: @cached, @lru_cache, Redis, memcached, .cache
    pattern = r'(^\s*@cached|^\s*@lru_cache|import redis|Redis\(|memcached|\.cache\(|cache\.get|cache\.set)'
    evidence = []

    for i, line in enumerate(file_text.split('\n'), 1):
        if _is_comment_line(line):
            continue
        if re.search(pattern, line, re.IGNORECASE):
            evidence.append({"file": file_name, "line": i})

    return (len(evidence) > 0, evidence)
