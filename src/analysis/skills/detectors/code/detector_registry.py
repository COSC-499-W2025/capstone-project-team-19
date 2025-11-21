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
)

# Only include detectors you want active.
# To remove any detector just remove it from this list
CORE_DETECTORS = [
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
]

CODE_DETECTOR_FUNCTIONS = {fn.__name__: fn for fn in CORE_DETECTORS}
