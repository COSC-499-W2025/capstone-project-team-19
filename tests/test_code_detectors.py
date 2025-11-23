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
    detect_assertions,
    detect_mocking_or_fixtures,
    detect_error_handling,
    detect_input_validation,
    detect_env_variable_usage,
    detect_crypto_usage,
    detect_mvc_folders,
    detect_api_routes,
    detect_components,
    detect_serialization,
    detect_database_queries,
    detect_caching,
)


# HELPER FUNCTIONS

def assert_detector_hits(detector, code, filename="test.py", min_evidence=1):
    """Assert that a detector finds patterns in code."""
    hit, evidence = detector(code, filename)
    assert hit is True, f"{detector.__name__} should detect pattern in code"
    assert len(evidence) >= min_evidence, f"Expected at least {min_evidence} evidence items"
    return evidence


def assert_detector_misses(detector, code, filename="test.py"):
    """Assert that a detector does NOT find patterns in code."""
    hit, evidence = detector(code, filename)
    assert hit is False, f"{detector.__name__} should not detect pattern in code"
    assert len(evidence) == 0, "Should have no evidence"


def assert_filename_detector_hits(detector, filename):
    """Assert that a filename-based detector matches."""
    hit, evidence = detector("", filename)
    assert hit is True, f"{detector.__name__} should detect {filename}"


def assert_filename_detector_misses(detector, filename):
    """Assert that a filename-based detector does not match."""
    hit, evidence = detector("", filename)
    assert hit is False, f"{detector.__name__} should not detect {filename}"


# OOP DETECTORS

def test_detect_classes():
    assert_detector_hits(detect_classes, "class User:\n    pass", min_evidence=1)
    assert_detector_misses(detect_classes, "def function(): pass")


def test_detect_inheritance():
    assert_detector_hits(detect_inheritance, "class Dog(Animal):\n    pass")
    assert_detector_hits(detect_inheritance, "class User extends BaseUser {}")
    assert_detector_misses(detect_inheritance, "class Simple:\n    pass")


def test_detect_polymorphism():
    code = "@override\ndef method(): pass\nvirtual void func() {}"
    assert_detector_hits(detect_polymorphism, code, min_evidence=2)
    assert_detector_misses(detect_polymorphism, "def regular(): pass")


# DATA STRUCTURE DETECTORS

def test_detect_hash_maps():
    code = 'user_data = dict()\nconfig = {"key": "value"}'
    assert_detector_hits(detect_hash_maps, code, min_evidence=2)
    assert_detector_misses(detect_hash_maps, "x = 5")


def test_detect_sets():
    code = "unique = set()\nitems = HashSet<Integer>()"
    assert_detector_hits(detect_sets, code, min_evidence=2)
    assert_detector_misses(detect_sets, "x = [1, 2, 3]")


def test_detect_queues_or_stacks():
    code = "stack = Stack()\nstack.push(item)\nqueue.pop()"
    assert_detector_hits(detect_queues_or_stacks, code, min_evidence=3)
    assert_detector_misses(detect_queues_or_stacks, "x = [1, 2, 3]")


# ALGORITHM DETECTORS

def test_detect_recursion():
    code = "def factorial(n):\n    return n * factorial(n - 1)"
    assert_detector_hits(detect_recursion, code)
    assert_detector_misses(detect_recursion, "def simple(n):\n    return n + 1")


def test_detect_sorting_or_search():
    code = "data.sort()\nresult = sorted(items)\nindex = binary_search(arr, target)"
    assert_detector_hits(detect_sorting_or_search, code, min_evidence=3)
    assert_detector_misses(detect_sorting_or_search, "x = [1, 2, 3]")


# CODE QUALITY DETECTORS

def test_detect_large_functions():
    large_func = "def large():\n" + "    x = 1\n" * 60
    assert_detector_hits(detect_large_functions, large_func)
    assert_detector_misses(detect_large_functions, "def small():\n    return 1")


def test_detect_comments_docstrings():
    code = '# Comment\ndef foo():\n    """Docstring"""\n    pass'
    assert_detector_hits(detect_comments_docstrings, code, min_evidence=2)
    assert_detector_misses(detect_comments_docstrings, "x = 5")


def test_detect_duplicate_code():
    # Stubbed out - should always return False
    hit, evidence = detect_duplicate_code("anything", "test.py")
    assert hit is False
    assert evidence == []


# STRUCTURE DETECTORS

def test_detect_modular_design():
    code = "import os\nfrom typing import List\nrequire('express')"
    assert_detector_hits(detect_modular_design, code, min_evidence=2)
    assert_detector_misses(detect_modular_design, "x = 5")


def test_detect_test_files():
    for filename in ["test_user.py", "user_test.py", "user.test.js", "src/tests/helper.py"]:
        assert_filename_detector_hits(detect_test_files, filename)
    for filename in ["main.py", "user.py", "component.js"]:
        assert_filename_detector_misses(detect_test_files, filename)


def test_detect_ci_workflows():
    for filename in [".github/workflows/test.yml", ".gitlab-ci.yml", "Jenkinsfile"]:
        assert_filename_detector_hits(detect_ci_workflows, filename)
    for filename in ["main.py", "workflow.txt"]:
        assert_filename_detector_misses(detect_ci_workflows, filename)


# TESTING DETECTORS

def test_detect_assertions():
    code = "assert x == 5\nexpect(result).toBe(true)\nshould.equal(a, b)"
    assert_detector_hits(detect_assertions, code, min_evidence=3)
    assert_detector_misses(detect_assertions, "x = 5")


def test_detect_mocking_or_fixtures():
    code = "@patch('module.func')\n@pytest.fixture\ndef mock_data():\n    return Mock()"
    assert_detector_hits(detect_mocking_or_fixtures, code, min_evidence=3)
    assert_detector_misses(detect_mocking_or_fixtures, "def regular(): pass")


# ERROR HANDLING & SECURITY DETECTORS

def test_detect_error_handling():
    code = "try:\n    risky()\nexcept Exception:\n    pass"
    assert_detector_hits(detect_error_handling, code, min_evidence=2)
    assert_detector_misses(detect_error_handling, "x = 5")


def test_detect_input_validation():
    code = "validate(email)\nschema.validate(data)\nif is_valid(input):"
    assert_detector_hits(detect_input_validation, code, min_evidence=2)
    assert_detector_misses(detect_input_validation, "x = 5")


def test_detect_env_variable_usage():
    code = "api_key = os.environ['KEY']\nport = process.env.PORT"
    assert_detector_hits(detect_env_variable_usage, code, min_evidence=2)
    assert_detector_misses(detect_env_variable_usage, "x = 5")


def test_detect_crypto_usage():
    code = "import hashlib\nencrypted = encrypt(data)\ntoken = jwt.encode(payload)"
    assert_detector_hits(detect_crypto_usage, code, min_evidence=3)
    assert_detector_misses(detect_crypto_usage, "x = 5")


# ARCHITECTURE DETECTORS

def test_detect_mvc_folders():
    for path in ["src/models/user.py", "app/views/index.js", "api/controllers/auth.py"]:
        assert_filename_detector_hits(detect_mvc_folders, path)
    assert_filename_detector_misses(detect_mvc_folders, "src/utils/helper.py")


def test_detect_api_routes():
    code = "@app.route('/api/users')\napp.get('/health')\n@GetMapping('/api/posts')"
    assert_detector_hits(detect_api_routes, code, min_evidence=3)
    assert_detector_misses(detect_api_routes, "def regular(): pass")


# FRONTEND DETECTORS

def test_detect_components():
    code = "class App extends Component {}\nVue.component('my-comp', {})"
    assert_detector_hits(detect_components, code, min_evidence=2)
    assert_detector_misses(detect_components, "const x = 5")


# BACKEND DETECTORS

def test_detect_serialization():
    code = "JSON.stringify(obj)\njson.dumps(data)\nserialize(model)"
    assert_detector_hits(detect_serialization, code, min_evidence=3)
    assert_detector_misses(detect_serialization, "x = 5")


def test_detect_database_queries():
    code = "SELECT * FROM users\ncursor.execute(query)\nUser.findOne({id: 1})"
    assert_detector_hits(detect_database_queries, code, min_evidence=3)
    assert_detector_misses(detect_database_queries, "x = 5")


def test_detect_caching():
    code = "@lru_cache\nredis.set('key', value)\ncache.get('data')"
    assert_detector_hits(detect_caching, code, min_evidence=2)
    assert_detector_misses(detect_caching, "x = 5")


# FALSE POSITIVE TESTS

def test_detect_classes_false_positives():
    """Ensure class detector doesn't trigger on non-class occurrences."""
    false_positives = [
        'message = "class User is defined"',  # String literal
        '# This class does something',  # Comment
        'my_class = 5',  # Variable name
        'user_class_name = "Admin"',  # Part of variable name
        "'''Documentation about class keyword'''",  # Docstring
    ]
    for code in false_positives:
        assert_detector_misses(detect_classes, code)


def test_detect_inheritance_false_positives():
    """Ensure inheritance detector doesn't trigger on non-inheritance patterns."""
    false_positives = [
        'class Simple:\n    pass',  # Class without inheritance
        'description = "class User(BaseUser)"',  # In string
        '# class Dog(Animal):',  # In comment
    ]
    for code in false_positives:
        assert_detector_misses(detect_inheritance, code)


def test_detect_hash_maps_false_positives():
    """Ensure hash map detector doesn't trigger on unrelated dict occurrences."""
    false_positives = [
        'dictionary = "dict"',  # String literal
        '# Using dict() here',  # Comment
        'predict = model.predict()',  # Similar word
        'verdict = get_verdict()',  # Contains 'dict'
    ]
    for code in false_positives:
        assert_detector_misses(detect_hash_maps, code)


def test_detect_recursion_false_positives():
    """Ensure recursion detector doesn't trigger on non-recursive functions."""
    false_positives = [
        'def process():\n    # factorial(n) is recursive',  # Comment
        'def calc():\n    result = "factorial(n)"',  # String
    ]
    for code in false_positives:
        assert_detector_misses(detect_recursion, code)

    # Note: def factorial() calling math.factorial() is an acceptable false positive
    # since the function name matches - would need full AST parsing to fix


def test_detect_sorting_false_positives():
    """Ensure sorting detector doesn't trigger on unrelated sort occurrences."""
    false_positives = [
        'resort = "vacation"',  # Contains 'sort'
        'assorted_items = []',  # Contains 'sorted'
        '"Please sort this list"',  # In string
        '# Use sorted() here',  # In comment
    ]
    for code in false_positives:
        assert_detector_misses(detect_sorting_or_search, code)


def test_detect_comments_false_positives():
    """Ensure comment detector doesn't trigger on # or // in strings."""
    false_positives = [
        'url = "http://example.com"',  # // in URL
        'tag = "This is a #hashtag"',  # # in string
        'regex = r"\\d+"',  # Escape sequences
    ]
    for code in false_positives:
        assert_detector_misses(detect_comments_docstrings, code)


def test_detect_modular_design_false_positives():
    """Ensure import detector doesn't trigger on import in strings/comments."""
    false_positives = [
        'message = "import this module"',  # In string
        '# import os',  # Commented out import
        'important = True',  # Contains 'import'
    ]
    for code in false_positives:
        assert_detector_misses(detect_modular_design, code)


def test_detect_error_handling_false_positives():
    """Ensure error handling detector doesn't trigger on try in strings."""
    false_positives = [
        'message = "try this approach"',  # In string
        '# try:',  # Commented code
        'country = "England"',  # Contains 'try'
        'retry_count = 3',  # Contains 'try'
    ]
    for code in false_positives:
        assert_detector_misses(detect_error_handling, code)


def test_detect_input_validation_false_positives():
    """Ensure validation detector doesn't trigger on validate in strings."""
    false_positives = [
        'message = "validate the input"',  # In string
        '# validate_email()',  # Comment
        'invalidate_cache()',  # Contains 'validate'
    ]
    for code in false_positives:
        assert_detector_misses(detect_input_validation, code)


def test_detect_crypto_false_positives():
    """Ensure crypto detector doesn't trigger on encrypt in strings."""
    false_positives = [
        'message = "encrypt the data"',  # In string
        '# hashlib.sha256()',  # Comment
        'decryption_key = None',  # Contains 'decrypt'
    ]
    for code in false_positives:
        assert_detector_misses(detect_crypto_usage, code)


def test_detect_api_routes_false_positives():
    """Ensure API route detector doesn't trigger on route in strings."""
    false_positives = [
        'message = "@app.route is a decorator"',  # In string
        '# @app.route("/api")',  # Comment
        'router = Router()',  # Variable name
    ]
    for code in false_positives:
        assert_detector_misses(detect_api_routes, code)


def test_detect_components_false_positives():
    """Ensure component detector doesn't trigger on Component in strings."""
    false_positives = [
        'message = "extends Component"',  # In string
        '# class App extends Component',  # Comment
        'component_name = "Header"',  # Variable name
    ]
    for code in false_positives:
        assert_detector_misses(detect_components, code)


def test_detect_caching_false_positives():
    """Ensure caching detector doesn't trigger on cache in strings."""
    false_positives = [
        'message = "clear the cache"',  # In string
        '# redis.set()',  # Comment
        'cached_data = None',  # Variable name
    ]
    for code in false_positives:
        assert_detector_misses(detect_caching, code)


# EDGE CASES

def test_all_detectors_handle_empty_input():
    """Test that all detectors handle empty input gracefully."""
    detectors = [
        detect_classes, detect_inheritance, detect_polymorphism,
        detect_hash_maps, detect_sets, detect_queues_or_stacks,
        detect_recursion, detect_sorting_or_search,
        detect_large_functions, detect_comments_docstrings, detect_duplicate_code,
        detect_modular_design, detect_assertions, detect_mocking_or_fixtures,
        detect_error_handling, detect_input_validation, detect_env_variable_usage,
        detect_crypto_usage, detect_api_routes, detect_components,
        detect_serialization, detect_database_queries, detect_caching,
    ]

    for detector in detectors:
        assert_detector_misses(detector, "")


def test_evidence_format():
    """Test that evidence has correct format."""
    evidence = assert_detector_hits(detect_classes, "class Test: pass")
    for item in evidence:
        assert "file" in item
        assert "line" in item
        assert item["file"] == "test.py"
        assert isinstance(item["line"], int)
        assert item["line"] > 0
