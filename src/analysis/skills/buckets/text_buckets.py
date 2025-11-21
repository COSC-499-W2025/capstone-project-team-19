from .bucket_types import SkillBucket

TEXT_SKILL_BUCKETS = [
    SkillBucket(
        name="clarity",
        total_signals=1,
        description="Clear communication",
        detectors=[
            "detect_sentence_clarity",
        ],
    ),

    SkillBucket(
        name="structure",
        total_signals=1,
        description="Structured writing",
        detectors=[
            "detect_paragraph_structure",
        ],
    ),

    SkillBucket(
        name="vocabulary",
        total_signals=1,
        description="Strong vocabulary",
        detectors=[
            "detect_vocabulary_diversity",
        ],
    ),

    SkillBucket(
        name="argumentation",
        total_signals=1,
        description="Analytical writing",
        detectors=[
            "detect_argument_structure",
        ],
    ),

    SkillBucket(
        name="depth",
        total_signals=1,
        description="Critical thinking",
        detectors=[
            "detect_depth_of_content",
        ],
    ),
    
    SkillBucket(
        name="process",
        total_signals=1,
        description="Revision & editing",
        detectors=[
            "detect_iterative_process",
        ],
    ),
    
    SkillBucket(
        name="planning",
        total_signals=1,
        description="Planning & organization",
        detectors=[
            "detect_planning_behavior",
        ],
    ),
    
    SkillBucket(
        name="research",
        total_signals=1,
        description="Research integration",
        detectors=[
            "detect_evidence_of_research",
        ],
    ),
    
    SkillBucket(
        name="data_collection",
        total_signals=1,
        description="Data collection",
        detectors=[
            "detect_data_collection",
        ],
    ),
    
    SkillBucket(
        name="data_analysis",
        total_signals=1,
        description="Data analysis",
        detectors=[
            "detect_data_analysis",
        ],
    ),
]