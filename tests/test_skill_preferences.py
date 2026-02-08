"""
tests/test_skill_preferences.py

Unit tests for the skill highlighting (skill preferences) functionality.
"""

import sqlite3
import pytest
from unittest.mock import patch

from src.db.skill_preferences import (
    get_user_skill_preferences,
    upsert_skill_preference,
    bulk_upsert_skill_preferences,
    clear_skill_preferences,
    get_all_user_skills,
    has_skill_preferences,
)
from src.services.skill_preferences_service import (
    get_available_skills_with_status,
    update_skill_preferences,
    get_highlighted_skills_for_display,
    reset_skill_preferences,
)


@pytest.fixture
def conn():
    """Create in-memory SQLite database with required tables."""
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_skill_preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            context TEXT NOT NULL CHECK (context IN ('global', 'portfolio', 'resume')),
            context_id INTEGER,
            skill_name TEXT NOT NULL,
            is_highlighted INTEGER DEFAULT 1,
            display_order INTEGER,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(user_id, context, context_id, skill_name)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS project_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_name TEXT NOT NULL,
            skill_name TEXT NOT NULL,
            level TEXT NOT NULL,
            score REAL NOT NULL,
            evidence_json TEXT,
            UNIQUE(user_id, project_name, skill_name)
        )
    """)
    conn.commit()
    yield conn
    conn.close()


@pytest.fixture
def conn_with_skills(conn):
    """Database with sample project skills."""
    skills = [
        (1, "project1", "algorithms", "Advanced", 1.0),
        (1, "project1", "data_structures", "Intermediate", 0.7),
        (1, "project1", "api_and_backend", "Advanced", 0.9),
        (1, "project2", "algorithms", "Beginner", 0.5),
        (1, "project2", "testing_and_ci", "Intermediate", 0.6),
    ]
    for user_id, project_name, skill_name, level, score in skills:
        conn.execute(
            "INSERT INTO project_skills (user_id, project_name, skill_name, level, score, evidence_json) VALUES (?, ?, ?, ?, ?, '[]')",
            (user_id, project_name, skill_name, level, score)
        )
    conn.commit()
    return conn


# Mock data for get_skill_events
MOCK_SKILL_EVENTS = [
    ("algorithms", "Advanced", 1.0, "project1", None, None),
    ("data_structures", "Intermediate", 0.7, "project1", None, None),
    ("api_and_backend", "Advanced", 0.9, "project1", None, None),
    ("algorithms", "Beginner", 0.5, "project2", None, None),
    ("testing_and_ci", "Intermediate", 0.6, "project2", None, None),
]


# =============================================================================
# Database Layer Tests
# =============================================================================

class TestUpsertSkillPreference:
    def test_insert_and_update(self, conn):
        # Insert
        upsert_skill_preference(conn, user_id=1, skill_name="algorithms", is_highlighted=True)
        prefs = get_user_skill_preferences(conn, user_id=1)
        assert len(prefs) == 1
        assert prefs[0]["is_highlighted"] is True

        # Update same skill
        upsert_skill_preference(conn, user_id=1, skill_name="algorithms", is_highlighted=False)
        prefs = get_user_skill_preferences(conn, user_id=1)
        assert len(prefs) == 1
        assert prefs[0]["is_highlighted"] is False

    def test_display_order(self, conn):
        upsert_skill_preference(conn, user_id=1, skill_name="c", display_order=3)
        upsert_skill_preference(conn, user_id=1, skill_name="a", display_order=1)
        upsert_skill_preference(conn, user_id=1, skill_name="b", display_order=2)

        prefs = get_user_skill_preferences(conn, user_id=1)
        assert [p["skill_name"] for p in prefs] == ["a", "b", "c"]


class TestBulkAndClear:
    def test_bulk_upsert(self, conn):
        bulk_upsert_skill_preferences(conn, user_id=1, preferences=[
            {"skill_name": "algorithms", "is_highlighted": True, "display_order": 1},
            {"skill_name": "data_structures", "is_highlighted": False},
        ])
        result = get_user_skill_preferences(conn, user_id=1)
        assert len(result) == 2

    def test_clear_preferences(self, conn):
        upsert_skill_preference(conn, user_id=1, skill_name="a")
        upsert_skill_preference(conn, user_id=1, skill_name="b")

        count = clear_skill_preferences(conn, user_id=1)
        assert count == 2
        assert get_user_skill_preferences(conn, user_id=1) == []


class TestContextFallback:
    def test_falls_back_to_global(self, conn):
        upsert_skill_preference(conn, user_id=1, skill_name="algorithms", context="global")

        # Query portfolio should fall back to global
        prefs = get_user_skill_preferences(conn, user_id=1, context="portfolio")
        assert len(prefs) == 1
        assert prefs[0]["skill_name"] == "algorithms"


class TestHasAndGetAllSkills:
    def test_has_skill_preferences(self, conn):
        assert has_skill_preferences(conn, user_id=1) is False
        upsert_skill_preference(conn, user_id=1, skill_name="algorithms")
        assert has_skill_preferences(conn, user_id=1) is True

    def test_get_all_user_skills(self, conn_with_skills):
        skills = get_all_user_skills(conn_with_skills, user_id=1)
        assert set(skills) == {"algorithms", "data_structures", "api_and_backend", "testing_and_ci"}


# =============================================================================
# Service Layer Tests
# =============================================================================

class TestGetAvailableSkillsWithStatus:
    @patch("src.services.skill_preferences_service.get_skill_events")
    def test_returns_all_skills_with_defaults(self, mock_get_skill_events, conn_with_skills):
        mock_get_skill_events.return_value = MOCK_SKILL_EVENTS
        skills = get_available_skills_with_status(conn_with_skills, user_id=1)

        assert len(skills) == 4
        for skill in skills:
            assert skill["is_highlighted"] is True

    @patch("src.services.skill_preferences_service.get_skill_events")
    def test_respects_stored_preferences(self, mock_get_skill_events, conn_with_skills):
        mock_get_skill_events.return_value = MOCK_SKILL_EVENTS
        upsert_skill_preference(conn_with_skills, user_id=1, skill_name="algorithms", is_highlighted=False)

        skills = get_available_skills_with_status(conn_with_skills, user_id=1)
        algo = next(s for s in skills if s["skill_name"] == "algorithms")
        assert algo["is_highlighted"] is False


class TestGetHighlightedSkillsForDisplay:
    def test_returns_all_when_no_preferences(self, conn_with_skills):
        skills = get_highlighted_skills_for_display(conn_with_skills, user_id=1)
        assert len(skills) == 4

    def test_excludes_hidden_skills(self, conn_with_skills):
        upsert_skill_preference(conn_with_skills, user_id=1, skill_name="algorithms", is_highlighted=False)

        skills = get_highlighted_skills_for_display(conn_with_skills, user_id=1)
        assert "algorithms" not in skills
        assert "data_structures" in skills

    def test_respects_display_order(self, conn_with_skills):
        bulk_upsert_skill_preferences(conn_with_skills, user_id=1, preferences=[
            {"skill_name": "testing_and_ci", "is_highlighted": True, "display_order": 1},
            {"skill_name": "algorithms", "is_highlighted": True, "display_order": 2},
        ])

        skills = get_highlighted_skills_for_display(conn_with_skills, user_id=1)
        assert skills[0] == "testing_and_ci"
        assert skills[1] == "algorithms"


class TestUpdateAndReset:
    @patch("src.services.skill_preferences_service.get_skill_events")
    def test_update_skill_preferences(self, mock_get_skill_events, conn_with_skills):
        mock_get_skill_events.return_value = MOCK_SKILL_EVENTS
        updates = [{"skill_name": "algorithms", "is_highlighted": False}]

        result = update_skill_preferences(conn_with_skills, user_id=1, skills=updates)
        algo = next(s for s in result if s["skill_name"] == "algorithms")
        assert algo["is_highlighted"] is False

    def test_reset_skill_preferences(self, conn_with_skills):
        bulk_upsert_skill_preferences(conn_with_skills, user_id=1, preferences=[
            {"skill_name": "algorithms", "is_highlighted": False},
        ])

        count = reset_skill_preferences(conn_with_skills, user_id=1)
        assert count == 1
        assert has_skill_preferences(conn_with_skills, user_id=1) is False


# =============================================================================
# Integration Test
# =============================================================================

class TestSkillHighlightingIntegration:
    @patch("src.services.skill_preferences_service.get_skill_events")
    def test_toggle_and_reset_flow(self, mock_get_skill_events, conn_with_skills):
        """Test complete flow: hide skills, verify hidden, reset, verify restored."""
        mock_get_skill_events.return_value = MOCK_SKILL_EVENTS

        # Initially all highlighted
        skills = get_highlighted_skills_for_display(conn_with_skills, user_id=1)
        assert len(skills) == 4

        # Hide two skills
        update_skill_preferences(conn_with_skills, user_id=1, skills=[
            {"skill_name": "algorithms", "is_highlighted": False},
            {"skill_name": "api_and_backend", "is_highlighted": False},
            {"skill_name": "data_structures", "is_highlighted": True},
            {"skill_name": "testing_and_ci", "is_highlighted": True},
        ])

        skills = get_highlighted_skills_for_display(conn_with_skills, user_id=1)
        assert "algorithms" not in skills
        assert "api_and_backend" not in skills
        assert len(skills) == 2

        # Reset
        reset_skill_preferences(conn_with_skills, user_id=1)
        skills = get_highlighted_skills_for_display(conn_with_skills, user_id=1)
        assert len(skills) == 4
