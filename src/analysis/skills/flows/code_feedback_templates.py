from typing import Dict

_DETECTOR_FEEDBACK: Dict[str, Dict[str, str]] = {
    "detect_classes": {
        "label": "Use class-based design where appropriate",
        "suggestion": "Introduce classes to encapsulate state/behavior (e.g., domain models, services) instead of purely script-style code.",
    },
    "detect_inheritance": {
        "label": "Demonstrate inheritance/abstraction (when appropriate)",
        "suggestion": "Use inheritance or interfaces/abstract base classes to share behavior across related types (only if it improves design).",
    },
    "detect_polymorphism": {
        "label": "Show polymorphism/overrides (when appropriate)",
        "suggestion": "Implement overridden methods or polymorphic interfaces (e.g., @Override, abstract methods) to demonstrate extensible design.",
    },
    "detect_hash_maps": {
        "label": "Use dictionary/map data structures",
        "suggestion": "Use dict/Map/HashMap for key→value lookups (e.g., caching, indexing, frequency counts) where it simplifies logic.",
    },
    "detect_sets": {
        "label": "Use set-based operations",
        "suggestion": "Use sets for uniqueness checks and fast membership testing (e.g., visited nodes, deduplication, permission scopes).",
    },
    "detect_queues_or_stacks": {
        "label": "Use stack/queue patterns (when suitable)",
        "suggestion": "Use stacks/queues/deques for DFS/BFS, backtracking, scheduling, or producer/consumer style workflows.",
    },
    "detect_recursion": {
        "label": "Demonstrate recursion (when suitable)",
        "suggestion": "Implement a recursive solution for naturally recursive problems (trees, DFS, divide-and-conquer) and document base cases.",
    },
    "detect_sorting_or_search": {
        "label": "Use sorting/searching patterns",
        "suggestion": "Use sorting or search utilities (sorted/.sort/binary search) when you need ordering, ranking, or efficient retrieval.",
    },
    "detect_large_functions": {
        "label": "Improve decomposition for large functions",
        "suggestion": "Split very large functions into smaller helpers (single responsibility) to improve readability, testability, and reuse.",
    },
    "detect_duplicate_code": {
        "label": "Reduce duplicated code",
        "suggestion": "Refactor repeated logic into shared helpers/modules to avoid copy-paste and make future changes safer.",
    },
    "detect_comments_docstrings": {
        "label": "Add documentation/comments",
        "suggestion": "Add docstrings/comments for non-obvious logic and public APIs; document inputs/outputs and tricky assumptions.",
    },
    "detect_modular_design": {
        "label": "Use modular structure",
        "suggestion": "Refactor into modules/packages and use imports to separate concerns (e.g., db, services, utils, routes).",
    },
    "detect_test_files": {
        "label": "Add test coverage",
        "suggestion": "Add unit/integration tests (e.g., pytest/unittest) under a tests/ folder and cover key edge cases.",
    },
    "detect_ci_workflows": {
        "label": "Add CI workflows",
        "suggestion": "Add a CI pipeline (e.g., GitHub Actions) to run formatting/linting/tests automatically on pushes and PRs.",
    },
    "detect_assertions": {
        "label": "Use assertions in tests",
        "suggestion": "Add explicit assertions/expectations in tests to validate outputs, error conditions, and invariants.",
    },
    "detect_mocking_or_fixtures": {
        "label": "Use fixtures/mocking in tests",
        "suggestion": "Use fixtures/mocks for isolation (e.g., patch external calls, seed test DB/state) to keep tests deterministic.",
    },
    "detect_error_handling": {
        "label": "Add robust error handling",
        "suggestion": "Use try/except (or language equivalents) around IO/network/DB operations and raise clear, actionable errors.",
    },
    "detect_input_validation": {
        "label": "Validate inputs",
        "suggestion": "Validate user/config/API inputs (schemas, validators, sanitize) and fail fast with clear messages.",
    },
    "detect_env_variable_usage": {
        "label": "Use environment configuration",
        "suggestion": "Move secrets/config to environment variables (.env) and document required keys; avoid hardcoding secrets.",
    },
    "detect_crypto_usage": {
        "label": "Demonstrate security primitives (when relevant)",
        "suggestion": "Use hashing/encryption/token verification where appropriate (password hashing, JWT validation, secure storage).",
    },
    "detect_mvc_folders": {
        "label": "Use a structured architecture (if applicable)",
        "suggestion": "Organize code into layers (models/views/controllers or equivalents) to separate data, UI, and logic concerns.",
    },
    "detect_api_routes": {
        "label": "Expose API routes/endpoints (if applicable)",
        "suggestion": "Implement basic API endpoints (e.g., REST routes) and structure routing cleanly (router/app.get/post).",
    },
    "detect_components": {
        "label": "Frontend components (if applicable)",
        "suggestion": "Add UI components (React/Vue/etc.) or component structure if this project includes a frontend.",
    },
    "detect_serialization": {
        "label": "Use serialization/data interchange",
        "suggestion": "Serialize/deserialize data (JSON, DTOs) for persistence or API boundaries and validate formats.",
    },
    "detect_database_queries": {
        "label": "Demonstrate DB interactions (if applicable)",
        "suggestion": "Add DB read/write operations (SQL/ORM) for persistence and ensure queries are parameterized.",
    },
    "detect_caching": {
        "label": "Use caching (if applicable)",
        "suggestion": "Add caching (lru_cache/Redis/memoization) where repeated computations or reads benefit from it.",
    },
}