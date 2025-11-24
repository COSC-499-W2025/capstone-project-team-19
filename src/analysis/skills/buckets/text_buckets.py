from .bucket_types import TextSkillBucket

TEXT_SKILL_BUCKETS = [
    TextSkillBucket(
        name="clarity",
        description="Clear communication",
        detectors=["detect_sentence_clarity"],
    ),
    TextSkillBucket(
        name="structure",
        description="Structured writing",
        detectors=["detect_paragraph_structure"],
    ),
    TextSkillBucket(
        name="vocabulary",
        description="Strong vocabulary",
        detectors=["detect_vocabulary_diversity"],
    ),
    TextSkillBucket(
        name="argumentation",
        description="Analytical writing",
        detectors=["detect_argument_structure"],
    ),
    TextSkillBucket(
        name="depth",
        description="Critical thinking",
        detectors=["detect_depth_of_content"],
    ),
    TextSkillBucket(
        name="process",
        description="Revision & editing",
        detectors=["detect_iterative_process"],
    ),
    TextSkillBucket(
        name="planning",
        description="Planning & organization",
        detectors=["detect_planning_behavior"],
    ),
    TextSkillBucket(
        name="research",
        description="Research integration",
        detectors=["detect_evidence_of_research"],
    ),
    TextSkillBucket(
        name="data_collection",
        description="Data collection",
        detectors=["detect_data_collection"],
    ),
    TextSkillBucket(
        name="data_analysis",
        description="Data analysis",
        detectors=["detect_data_analysis"],
    ),
]
