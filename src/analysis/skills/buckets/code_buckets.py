from .bucket_types import SkillBucket

CODE_SKILL_BUCKETS = [
    SkillBucket(
        name="object_oriented_programming",
        total_signals=5,
        description="Ability to design using OOP principles (classes, inheritance, polymorphism, abstraction, encapsulation).",
        detectors=[
            "detect_classes",
            "detect_inheritance",
            "detect_polymorphism",
            "detect_abstraction",
            "detect_encapsulation"
        ],
    ),

    SkillBucket(
        name="data_structures",
        total_signals=6,
        description="Use of appropriate data structures (lists, sets, dicts, stacks, queues, heaps, graphs, trees).",
        detectors=[
            "detect_hash_maps",
            "detect_sets",
            "detect_queues",
            "detect_stacks",
            "detect_heaps",
            "detect_graph_structures"
        ],
    ),

    SkillBucket(
        name="algorithms",
        total_signals=6,
        description="Use of algorithmic thinking (recursion, searching, sorting, DP, BFS/DFS).",
        detectors=[
            "detect_recursion",
            "detect_binary_search",
            "detect_sorting",
            "detect_bfs",
            "detect_dfs",
            "detect_dynamic_programming"
        ],
    ),

    SkillBucket(
        name="architecture_and_design",
        total_signals=5,
        description="Large-scale structural design: MVC, modularity, API routes, services, layered architecture.",
        detectors=[
            "detect_mvc_folders",
            "detect_modular_design",
            "detect_api_routes",
            "detect_layered_architecture",
            "detect_component_structure"
        ],
    ),

    SkillBucket(
        name="clean_code_and_quality",
        total_signals=6,
        description="Code maintainability, clarity, complexity, naming practices, documentation.",
        detectors=[
            "detect_cyclomatic_complexity",
            "detect_maintainability_index",
            "detect_large_functions",
            "detect_naming_conventions",
            "detect_comments_docstrings",
            "detect_duplicate_code"
        ],
    ),

    SkillBucket(
        name="testing_and_ci",
        total_signals=4,
        description="Testing practices and continuous integration.",
        detectors=[
            "detect_test_files",
            "detect_assertions",
            "detect_ci_workflows",
            "detect_mocking_or_fixtures"
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
            "detect_crypto_usage"
        ],
    ),

    SkillBucket(
        name="frontend_skills",
        total_signals=4,
        description="Frontend development using React/Vue/HTML/CSS/JS.",
        detectors=[
            "detect_components",
            "detect_state_management",
            "detect_responsive_design",
            "detect_semantic_html"
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
            "detect_caching"
        ],
    )
]