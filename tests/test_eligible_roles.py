"""
Tests for eligible role filtering feature.

Tests cover:
1. get_eligible_roles logic in role_eligibility.py
"""

import pytest


class TestGetEligibleRoles:

    def test_returns_all_code_roles_when_no_scores(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles, CODE_ROLES
        roles = get_eligible_roles("code", None)
        assert sorted(roles) == sorted(CODE_ROLES.keys())

    def test_returns_all_text_roles_when_no_scores(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles, TEXT_ROLES
        roles = get_eligible_roles("text", None)
        assert sorted(roles) == sorted(TEXT_ROLES.keys())

    def test_returns_all_roles_when_scores_empty(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles, CODE_ROLES
        roles = get_eligible_roles("code", {})
        assert sorted(roles) == sorted(CODE_ROLES.keys())

    def test_filters_code_roles_by_bucket_scores(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles
        scores = {
            "algorithms": 0.6,
            "data_structures": 0.5,
            "api_and_backend": 0.0,
            "frontend_skills": 0.0,
            "architecture_and_design": 0.0,
            "testing_and_ci": 0.0,
            "security_and_error_handling": 0.0,
            "clean_code_and_quality": 0.0,
            "object_oriented_programming": 0.0,
        }
        roles = get_eligible_roles("code", scores)
        assert "Algorithms Engineer" in roles
        assert "Data Engineer" in roles
        assert "Backend Developer" not in roles
        assert "Frontend Developer" not in roles

    def test_filters_text_roles_by_bucket_scores(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles
        scores = {
            "research": 0.6,
            "argumentation": 0.4,
            "clarity": 0.0,
            "structure": 0.0,
            "depth": 0.0,
            "vocabulary": 0.0,
            "process": 0.0,
            "planning": 0.0,
            "data_analysis": 0.0,
            "data_collection": 0.0,
        }
        roles = get_eligible_roles("text", scores)
        assert "Researcher" in roles
        assert "Research Analyst" in roles
        assert "Lead Author" not in roles
        assert "Data Analyst" not in roles

    def test_falls_back_to_all_roles_when_nothing_qualifies(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles, CODE_ROLES
        scores = {k: 0.0 for k in [
            "algorithms", "data_structures", "api_and_backend",
            "frontend_skills", "architecture_and_design", "testing_and_ci",
            "security_and_error_handling", "clean_code_and_quality",
            "object_oriented_programming",
        ]}
        roles = get_eligible_roles("code", scores)
        assert sorted(roles) == sorted(CODE_ROLES.keys())

    def test_unknown_project_type_defaults_to_code_roles(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles, CODE_ROLES
        roles = get_eligible_roles("unknown", None)
        assert sorted(roles) == sorted(CODE_ROLES.keys())

    def test_single_role_eligible_when_only_one_threshold_met(self):
        from src.analysis.skills.roles.role_eligibility import get_eligible_roles
        scores = {
            "frontend_skills": 0.5,
            "api_and_backend": 0.0,
            "algorithms": 0.0,
            "data_structures": 0.0,
            "architecture_and_design": 0.0,
            "testing_and_ci": 0.0,
            "security_and_error_handling": 0.0,
            "clean_code_and_quality": 0.0,
            "object_oriented_programming": 0.0,
        }
        roles = get_eligible_roles("code", scores)
        assert "Frontend Developer" in roles
        assert "Backend Developer" not in roles
        assert "Full-Stack Developer" not in roles