from .bucket_types import SkillBucket

CODE_SKILL_BUCKETS = [
    SkillBucket(
        name="object_oriented_programming",
        total_signals=3,
        description="Ability to design using OOP principles (classes, inheritance, polymorphism).",
        detectors=[
            "detect_classes",
            "detect_inheritance",
            "detect_polymorphism",
        ],
    ),

    SkillBucket(
        name="data_structures",
        total_signals=3,
        description="Use of appropriate data structures (hash maps, sets, queues/stacks).",
        detectors=[
            "detect_hash_maps",
            "detect_sets",
            "detect_queues_or_stacks",
        ],
    ),

    SkillBucket(
        name="algorithms",
        total_signals=2,
        description="Use of algorithmic thinking (recursion, searching, sorting).",
        detectors=[
            "detect_recursion",
            "detect_sorting_or_search",
        ],
    ),

    SkillBucket(
        name="architecture_and_design",
        total_signals=3,
        description="Large-scale structural design: MVC, modularity, API routes.",
        detectors=[
            "detect_mvc_folders",
            "detect_modular_design",
            "detect_api_routes",
        ],
    ),

    SkillBucket(
        name="clean_code_and_quality",
        total_signals=3,
        description="Code maintainability, clarity, complexity, documentation.",
        detectors=[
            "detect_large_functions",
            "detect_comments_docstrings",
            "detect_duplicate_code",
        ],
        weights={
            "detect_large_functions": -1,      # negative: large functions are bad
            "detect_comments_docstrings": 1,   # positive: comments are good
            "detect_duplicate_code": -1,       # negative: duplicates are bad
        },
    ),

    SkillBucket(
        name="testing_and_ci",
        total_signals=4,
        description="Testing practices and continuous integration.",
        detectors=[
            "detect_test_files",
            "detect_assertions",
            "detect_ci_workflows",
            "detect_mocking_or_fixtures",
        ],
    ),

    SkillBucket(
        name="security_and_error_handling",
        total_signals=4,
        description="Error handling, secure coding, input validation, environment variables.",
        detectors=[
            "detect_error_handling",
            "detect_input_validation",
            "detect_env_variable_usage",
            "detect_crypto_usage",
        ],
    ),

    SkillBucket(
        name="frontend_skills",
        total_signals=1,
        description="Frontend development using React/Vue components.",
        detectors=[
            "detect_components",
        ],
    ),

    SkillBucket(
        name="api_and_backend",
        total_signals=4,
        description="Backend skills: routing, serialization, database interaction, caching.",
        detectors=[
            "detect_api_routes",
            "detect_serialization",
            "detect_database_queries",
            "detect_caching",
        ],
    )
]
