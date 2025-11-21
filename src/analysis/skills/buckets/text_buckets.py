from .bucket_types import SkillBucket

TEXT_SKILL_BUCKETS = [
    SkillBucket(
        name="clarity",
        total_signals=4,
        description="Clear, concise writing with minimal ambiguity.",
        detectors=[
            "detect_plain_language",
            "detect_sentence_clarity",
            "detect_precision_keywords",
            "detect_readability_metrics"
        ],
    ),

    SkillBucket(
        name="technical_writing",
        total_signals=5,
        description="Ability to explain technical concepts effectively.",
        detectors=[
            "detect_technical_terms",
            "detect_algorithm_descriptions",
            "detect_system_explanations",
            "detect_data_description",
            "detect_correct_usage_of_CS_vocabulary"
        ],
    ),

    SkillBucket(
        name="organization",
        total_signals=4,
        description="Logical structure: intro, body, conclusion, headings, flow.",
        detectors=[
            "detect_headings",
            "detect_document_structure",
            "detect_logical_flow",
            "detect_paragraph_transitions"
        ],
    ),

    SkillBucket(
        name="argumentation_and_reasoning",
        total_signals=4,
        description="Critical thinking, argument support, evidence use.",
        detectors=[
            "detect_claim_evidence_pattern",
            "detect_argument_markers",
            "detect_cause_effect_reasoning",
            "detect_conclusion_markers"
        ],
    ),

    SkillBucket(
        name="domain_expertise",
        total_signals=4,
        description="Evidence of subject-matter knowledge through vocabulary and concepts.",
        detectors=[
            "detect_domain_keywords",
            "detect_topic_model_alignment",
            "detect_correct_use_of_theory",
            "detect_contextual_accuracy"
        ],
    )
]