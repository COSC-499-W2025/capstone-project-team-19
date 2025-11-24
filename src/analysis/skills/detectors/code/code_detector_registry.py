"""
This file collects and registers the detector functions for code projects.

The registry pattern allows:
- adding detectors easily
- removing detectors by deleting 1 line here
- running all detectors automatically
- avoiding circular imports
"""

from .code_detectors import (
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

# Only include detectors you want active.
# To remove any detector just remove it from this list
CORE_DETECTORS = [
    # OOP
    detect_classes,
    detect_inheritance,
    detect_polymorphism,

    # Data Structures
    detect_hash_maps,
    detect_sets,
    detect_queues_or_stacks,

    # Algorithms
    detect_recursion,
    detect_sorting_or_search,

    # Code Quality
    detect_large_functions,
    detect_comments_docstrings,
    detect_duplicate_code,

    # Architecture
    detect_modular_design,
    detect_mvc_folders,
    detect_api_routes,

    # Testing & CI
    detect_test_files,
    detect_ci_workflows,
    detect_assertions,
    detect_mocking_or_fixtures,

    # Security & Error Handling
    detect_error_handling,
    detect_input_validation,
    detect_env_variable_usage,
    detect_crypto_usage,

    # Frontend
    detect_components,

    # Backend
    detect_serialization,
    detect_database_queries,
    detect_caching,
]

CODE_DETECTOR_FUNCTIONS = {fn.__name__: fn for fn in CORE_DETECTORS}
