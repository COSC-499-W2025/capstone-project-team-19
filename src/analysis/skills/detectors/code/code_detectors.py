"""
Basic detector function stubs.

Each detector should return:
    (hit: bool, evidence: list[dict])
"""

import re
from typing import Tuple, List, Dict

# Compiling patterns with regex (one per detector for all lines instead of one per detector per line)
PY_DICT_PATTERN = re.compile(r'^\s*\w+\s*=\s*(dict\s*\(|\{\s*["\']?\w+["\']?\s*:)', re.IGNORECASE)
JAVA_MAP_PATTERN = re.compile(r'\b(HashMap|Map<\w+,\s*\w+>)', re.IGNORECASE)
JS_MAP_PATTERN = re.compile(r'\bnew\s+Map\s*\(', re.IGNORECASE)
JS_OBJECT_LITERAL = re.compile(r'^\s*\w+\s*=\s*\{\s*\w+\s*:.*\}$')
FALSE_MAP_IDENTIFIER = re.compile(r'\w*map\w*', re.IGNORECASE)
QUEUE_STACK_PATTERN = re.compile(r'(Queue|Stack|Deque|\.push\(|\.pop\(|\.enqueue|\.dequeue)')
RECURSION_PATTERN = re.compile(r'(def|function|func)\s+(\w+)\s*\(')
SORT_SEARCH_PATTERN = re.compile(r'(\.sort\(|\bsorted\(|Arrays\.sort|Collections\.sort|binary.?search|linear.?search)', re.IGNORECASE)
LARGE_FUNCTION_PATTERN = re.compile(r'^\s*(def|function|func|public|private|protected)\s+\w+\s*\(')
COMMENT_DOCSTRING_PATTERN = re.compile(r'(^\s*#|^\s*//|/\*|\"\"\"|\'\'\'|<!--)')
MODULAR_PATTERN = re.compile(r'(^import\s+|^from\s+.*\s+import|^require\(|^#include)')
TEST_PATTERN = re.compile(r'(test_|_test\.|spec\.|\.test\.|__tests__|/tests?/)', re.IGNORECASE)
CI_WORKFLOW_PATTERN = re.compile(r'(\.github/workflows/|\.gitlab-ci\.|Jenkinsfile|\.circleci/|\.travis\.yml)')
ASSERTION_PATTERN = re.compile(r'(\bassert\b|expect\(|should\.|chai\.)', re.IGNORECASE)
MOCKING_FIXTURE_PATTERN = re.compile(r'(mock|Mock|@patch|@fixture|stub|@pytest\.fixture)')
ERROR_HANDLING_PATTERN = re.compile(r'(^\s*try:|^\s*except\b|catch\s*\(|throw\s+new|raises\()', re.IGNORECASE)
INPUT_VALIDATOR_PATTERN = re.compile(r'(\bvalidate\(|validator|sanitize\(|schema\.validate|\.is_valid\()', re.IGNORECASE)
ENV_USAGE_PATTERN = re.compile(r'(process\.env|os\.environ|\bgetenv\(|import dotenv|load_dotenv)')
CRYPTO_PATTERN = re.compile(r'(import hashlib|import bcrypt|crypto\.|encrypt\(|decrypt\(|jwt\.|hashlib\.|bcrypt\.)', re.IGNORECASE)
MVC_PATTERN = re.compile(r'/(models|views|controllers)/', re.IGNORECASE)
API_ROUTES_PATTERN = re.compile(r'(^\s*@app\.route|^\s*@router\.|^\s*@(Get|Post|Put|Delete)Mapping|app\.(get|post|put|delete)\()')
COMPONENTS_PATTERN = re.compile(r'(React\.Component|class \w+ extends Component|Vue\.component|^\s*@Component|createComponent)')
SERIALIZATION_PATTERN = re.compile(r'(JSON\.stringify|json\.dumps|\bserialize\(|\.toJSON\(|JsonSerializer|pickle\.dump)')
DB_QUERY_PATTERN = re.compile(r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|cursor\.execute|\.query\(|\.findOne|\.findMany|\.find\(|\.save\()')
CACHING_PATTERN = re.compile(r'(^\s*@cached|^\s*@lru_cache|import redis|Redis\(|memcached|\.cache\(|cache\.get|cache\.set)')
SETS_PATTERN = re.compile(r'(HashSet|set\(|Set<|\bset\s*=)')
CLASSES_PATTERN = re.compile(r'^\s*class\s+\w+')
INHERITANCE_PATTERN = re.compile(r'^\s*(class\s+\w+\s*\([^)]+\)|class\s+\w+\s+extends\s+\w+|class\s+\w+\s*:\s*(public|private|protected))')
POLYMORPHISM_PATTERN = re.compile(r'(@override|@Override|virtual\s+\w+|abstract\s+class|abstract\s+def)', re.IGNORECASE)

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

def detect_classes(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect class definitions such as `class Foo:`."""
    # Must be at start of line (possibly after whitespace) to avoid strings/comments
    for i, line in enumerate(lines, 1):
        if CLASSES_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_inheritance(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect class inheritance such as `class Foo(Bar):`."""
    # Matches: class Dog(Animal), class User extends Base, class Foo : public Bar
    # Must have something in parentheses or 'extends' keyword
    # Must be at start of line to avoid strings
    for i, line in enumerate(lines, 1):
        if INHERITANCE_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_polymorphism(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect overridden methods or same method names across classes."""
    # Matches: @override, @Override, virtual void, abstract class
    for i, line in enumerate(lines, 1):
        if POLYMORPHISM_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# DATA STRUCTURE DETECTORS

def detect_hash_maps(lines: List[str], file_name: str):
    # Regex rules:
    # 1. Detect Python dict usage: x = {}  OR x = dict(...)
    # Allow both quoted and unquoted keys: {"key": ...} or {key: ...}

    # 2. Detect Java / C# HashMap, Map<K,V>

    # 3. Detect JavaScript/TypeScript Map()

    # Helper: pattern to skip JS object literals:  foo = { a:1 }
    # Only skip if it's clearly a JS object (single line with closing brace)

    # Helper: avoid identifiers containing "map" (heatmap, mymap, colormap)

    for i, line in enumerate(lines, 1):
        stripped = line.strip()

        # Skip comments
        if stripped.startswith("#") or stripped.startswith("//") or stripped.startswith("/*"):
            continue

        # Skip strings
        if stripped.startswith(("'", '"')):
            continue

        # Avoid JS object literal false positives
        if JS_OBJECT_LITERAL.search(stripped):
            continue

        # Avoid variable names that contain "map"
        # unless it's actually Map<K,V>, HashMap, or new Map()
        if FALSE_MAP_IDENTIFIER.search(stripped) and not (JAVA_MAP_PATTERN.search(stripped) or JS_MAP_PATTERN.search(stripped)):
            continue

        # Now check actual hashmap patterns
        if (
            PY_DICT_PATTERN.search(stripped)
            or JAVA_MAP_PATTERN.search(stripped)
            or JS_MAP_PATTERN.search(stripped)
        ):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_sets(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect set literals, set() calls, or other set usage."""
    # Matches: HashSet, set(), Set<String>, set =
    for i, line in enumerate(lines, 1):
        if SETS_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_queues_or_stacks(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """
    Detect simple queue/stack usage (append/pop patterns or collections.deque).
    """
    # Matches: Queue, Stack, Deque, .push(), .pop(), .enqueue, .dequeue
    for i, line in enumerate(lines, 1):
        if QUEUE_STACK_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# ALGORITHM DETECTORS

def detect_recursion(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect recursive function calls."""
    # Find function definitions and track their names
    current_function = None
    function_start_line = 0

    for i, line in enumerate(lines, 1):
        # Check if this line defines a function
        match = RECURSION_PATTERN.search(line)
        if match:
            current_function = match.group(2)
            function_start_line = i

        # If we're inside a function, check if it calls itself
        if current_function:
            # Look for the function name followed by a parenthesis (function call)
            call_pattern = f"{current_function}("
            if call_pattern in line and i != function_start_line:
                return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_sorting_or_search(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect calls to `sort`, `sorted`, or binary search patterns."""
    # Matches: .sort(), sorted(), Arrays.sort, Collections.sort, binary_search, binarySearch
    for i, line in enumerate(lines, 1):
        # Skip comment lines
        stripped = line.strip()
        if stripped.startswith('#') or stripped.startswith('//'):
            continue
        if SORT_SEARCH_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# CODE QUALITY DETECTORS

def detect_large_functions(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect very long functions that may indicate low-quality structure."""
    # Pattern to detect function definitions
    function_starts = []
    for i, line in enumerate(lines):
        if LARGE_FUNCTION_PATTERN.search(line):
            function_starts.append(i)

    # Check function lengths (threshold: 50 lines)
    for idx, start in enumerate(function_starts):
        if idx + 1 < len(function_starts):
            end = function_starts[idx + 1]
        else:
            end = len(lines)

        function_length = end - start
        if function_length > 50:
            return (True, [{"file": file_name, "line": start + 1}])

    return (False, [])


def detect_comments_docstrings(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect comments or docstrings for clarity/documentation."""
    # Matches: #, //, /* */, """, ''', <!--
    for i, line in enumerate(lines, 1):
        if COMMENT_DOCSTRING_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_duplicate_code(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect repeated code blocks (basic duplicate detection)."""
    # To be implemented in another PR due to complexity.
    return False, []


# STRUCTURE / SOFTWARE ENGINEERING

def detect_modular_design(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect evidence of modular design (imports, multiple modules)."""
    # Matches: import, from X import, require(), #include
    for i, line in enumerate(lines, 1):
        if MODULAR_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_test_files(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect pytest/unittest test cases or test file naming."""
    # Check filename patterns: test_, _test., spec., .test., __tests__, /tests/

    if TEST_PATTERN.search(file_name):
        return True, [{"file": file_name, "line": 0}]

    return False, []


def detect_ci_workflows(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect presence of CI/CD workflow configs (GitHub Actions)."""
    # Check filepath patterns: .github/workflows/, .gitlab-ci., Jenkinsfile, .circleci/, .travis.yml

    if CI_WORKFLOW_PATTERN.search(file_name):
        return True, [{"file": file_name, "line": 0}]

    return False, []


# TESTING DETECTORS

def detect_assertions(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect test assertions."""
    # Matches: assert, expect, should, chai.
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if ASSERTION_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_mocking_or_fixtures(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect mocking or fixture usage in tests."""
    # Matches: mock, Mock, @patch, fixture, stub
    for i, line in enumerate(lines, 1):
        if MOCKING_FIXTURE_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# ERROR HANDLING & SECURITY

def detect_error_handling(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect error handling patterns."""
    # Matches: try:, except, catch, throw, raises
    # Must be at start of line or after whitespace for try/except
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if ERROR_HANDLING_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_input_validation(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect input validation patterns."""
    # Matches: validate, validator, sanitize, schema.validate
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if INPUT_VALIDATOR_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_env_variable_usage(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect environment variable usage."""
    # Matches: process.env, os.environ, getenv, .env (but not "environment" variable)
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if ENV_USAGE_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_crypto_usage(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect cryptography and security library usage."""
    # Matches: hashlib, bcrypt, crypto imports/usage, encrypt/decrypt functions
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if CRYPTO_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# ARCHITECTURE DETECTORS

def detect_mvc_folders(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect MVC folder structure."""
    # Check filepath for models, views, controllers folders

    if MVC_PATTERN.search(file_name):
        return True, [{"file": file_name, "line": 0}]

    return False, []


def detect_api_routes(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect API route definitions."""
    # Matches: @app.route, @router., app.get(, @GetMapping, @PostMapping
    # Must be at start of line (decorator) or actual function call
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if API_ROUTES_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# FRONTEND DETECTORS

def detect_components(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect frontend component usage."""
    # Matches: React.Component, extends Component, Vue.component, @Component
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if COMPONENTS_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


# BACKEND DETECTORS

def detect_serialization(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect data serialization patterns."""
    # Matches: JSON.stringify, json.dumps, serialize, toJSON, JsonSerializer
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if SERIALIZATION_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_database_queries(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect database query usage."""
    # Matches: SELECT, INSERT, UPDATE, cursor.execute, query(, findOne
    # For SQL keywords, require word boundaries or start of string
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if DB_QUERY_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])


def detect_caching(lines: List[str], file_name: str) -> Tuple[bool, List[Dict]]:
    """Detect caching implementation."""
    # Matches: @cached, @lru_cache, Redis, memcached, .cache
    for i, line in enumerate(lines, 1):
        if _is_comment_line(line):
            continue
        if CACHING_PATTERN.search(line):
            return (True, [{"file": file_name, "line": i}])

    return (False, [])
