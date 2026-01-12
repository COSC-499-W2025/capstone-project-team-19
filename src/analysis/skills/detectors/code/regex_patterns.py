import re

# Data structures
PY_DICT_PATTERN = re.compile(r'^\s*\w+\s*=\s*(dict\s*\(|\{\s*["\']?\w+["\']?\s*:)', re.IGNORECASE)
JAVA_MAP_PATTERN = re.compile(r'\b(HashMap|Map<\w+,\s*\w+>)', re.IGNORECASE)
JS_MAP_PATTERN = re.compile(r'\bnew\s+Map\s*\(', re.IGNORECASE)
JS_OBJECT_LITERAL = re.compile(r'^\s*\w+\s*=\s*\{\s*\w+\s*:.*\}$')
FALSE_MAP_IDENTIFIER = re.compile(r'\w*map\w*', re.IGNORECASE)

# Queues & stacks
QUEUE_STACK_PATTERN = re.compile(r'(Queue|Stack|Deque|\.push\(|\.pop\(|\.enqueue|\.dequeue)', re.IGNORECASE)

# Recursion
RECURSION_PATTERN = re.compile(r'(def|function|func)\s+(\w+)\s*\(')

# Sort & search
SORT_SEARCH_PATTERN = re.compile(r'(\.sort\(|\bsorted\(|Arrays\.sort|Collections\.sort|binary.?search|linear.?search)', re.IGNORECASE)

# Large function declaration
LARGE_FUNCTION_PATTERN = re.compile(r'^\s*(def|function|func|public|private|protected)\s+\w+\s*\(')

# Comments/docstrings
COMMENT_DOCSTRING_PATTERN = re.compile(r'(^\s*#|^\s*//|/\*|\"\"\"|\'\'\'|<!--)')

# Modularity (imports/includes)
MODULAR_PATTERN = re.compile(r'(^import\s+|^from\s+.*\s+import|^require\(|^#include)')

# Tests
TEST_PATTERN = re.compile(r'(test_|_test\.|spec\.|\.test\.|__tests__|/tests?/)', re.IGNORECASE)

# CI/CD
CI_WORKFLOW_PATTERN = re.compile(r'(\.github/workflows/|\.gitlab-ci\.|Jenkinsfile|\.circleci/|\.travis\.yml)')

# Assertions
ASSERTION_PATTERN = re.compile(r'(\bassert\b|expect\(|should\.|chai\.)', re.IGNORECASE)

# Mocking/fixtures
MOCKING_FIXTURE_PATTERN = re.compile(r'(mock|Mock|@patch|@fixture|stub|@pytest\.fixture)', re.IGNORECASE)

# Error handling
ERROR_HANDLING_PATTERN = re.compile(r'(^\s*try:|^\s*except\b|catch\s*\(|throw\s+new|raises\()', re.IGNORECASE)

# Input validation
INPUT_VALIDATOR_PATTERN = re.compile(r'(\bvalidate\(|validator|sanitize\(|schema\.validate|\.is_valid\()', re.IGNORECASE)

# Environment variables
ENV_USAGE_PATTERN = re.compile(r'(process\.env|os\.environ|\bgetenv\(|import dotenv|load_dotenv)', re.IGNORECASE)

# Cryptography
CRYPTO_PATTERN = re.compile(r'(import hashlib|import bcrypt|crypto\.|encrypt\(|decrypt\(|jwt\.|hashlib\.|bcrypt\.)', re.IGNORECASE)

# MVC
MVC_PATTERN = re.compile(r'/(models|views|controllers)/', re.IGNORECASE)

# API routes
API_ROUTES_PATTERN = re.compile(r'(^\s*@app\.route|^\s*@router\.|^\s*@(Get|Post|Put|Delete)Mapping|app\.(get|post|put|delete)\()')

# Components
COMPONENTS_PATTERN = re.compile(r'(React\.Component|class \w+ extends Component|Vue\.component|^\s*@Component|createComponent)')

# Serialization
SERIALIZATION_PATTERN = re.compile(r'(JSON\.stringify|json\.dumps|\bserialize\(|\.toJSON\(|JsonSerializer|pickle\.dump)')

# Database queries
DB_QUERY_PATTERN = re.compile(r'(\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b|cursor\.execute|\.query\(|\.findOne|\.findMany|\.find\(|\.save\()', re.IGNORECASE)

# Caching
CACHING_PATTERN = re.compile(r'(^\s*@cached|^\s*@lru_cache|import redis|Redis\(|memcached|\.cache\(|cache\.get|cache\.set)', re.IGNORECASE)

# Sets
SETS_PATTERN = re.compile(r'(HashSet|set\(|Set<|\bset\s*=)')

# Classes
CLASSES_PATTERN = re.compile(r'^\s*class\s+\w+')

# Inheritance
INHERITANCE_PATTERN = re.compile(r'^\s*(class\s+\w+\s*\([^)]+\)|class\s+\w+\s+extends\s+\w+|class\s+\w+\s*:\s*(public|private|protected))')

# Polymorphism
POLYMORPHISM_PATTERN = re.compile(r'(@override|@Override|virtual\s+\w+|abstract\s+class|abstract\s+def)', re.IGNORECASE)