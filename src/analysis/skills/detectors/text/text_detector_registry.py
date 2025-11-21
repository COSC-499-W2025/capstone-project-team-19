"""
This file collects and registers the detector functions for text projects.
"""

from .text_detectors import (    
    detect_sentence_clarity,
    detect_paragraph_structure,
    detect_vocabulary_diversity,
    detect_argument_structure,
    detect_depth_of_content,
    detect_iterative_process,
    detect_planning_behavior,
    detect_evidence_of_research,
    detect_data_collection,
    detect_data_analysis,
)

# Only include detectors you want active.
# To remove any detector just remove it from this list
CORE_DETECTORS = [
    detect_sentence_clarity,
    detect_paragraph_structure,
    detect_vocabulary_diversity,
    detect_argument_structure,
    detect_depth_of_content,
    detect_iterative_process,
    detect_planning_behavior,
    detect_evidence_of_research,
    detect_data_collection,
    detect_data_analysis,
]

TEXT_DETECTOR_FUNCTIONS = {fn.__name__: fn for fn in CORE_DETECTORS}