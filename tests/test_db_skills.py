import sqlite3
import json
import pytest
from src.db.skills import insert_project_skill, get_project_skills


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    conn.execute("""
        CREATE TABLE projects (
            project_key INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            display_name TEXT NOT NULL,
            classification TEXT,
            project_type TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE project_skills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            project_key INTEGER NOT NULL,
            skill_name TEXT NOT NULL,
            level TEXT NOT NULL,
            score REAL NOT NULL,
            evidence_json TEXT,
            UNIQUE(user_id, project_key, skill_name)
        )
    """)
    conn.commit()
    yield conn
    conn.close()


def test_get_project_skills_returns_ordered_by_score(conn):
    insert_project_skill(conn, 1, "proj1", "skill1", "Beginner", 0.3, json.dumps([]))
    insert_project_skill(conn, 1, "proj1", "skill2", "Advanced", 1.0, json.dumps([]))
    insert_project_skill(conn, 1, "proj1", "skill3", "Intermediate", 0.6, json.dumps([]))

    rows = get_project_skills(conn, 1, "proj1")
    assert len(rows) == 3
    assert rows[0][0] == "skill2"  # Highest score first
    assert rows[0][2] == 1.0
    assert rows[1][0] == "skill3"
    assert rows[2][0] == "skill1"


def test_get_project_skills_returns_empty_when_none(conn):
    rows = get_project_skills(conn, 1, "nonexistent")
    assert rows == []


def test_get_project_skills_returns_correct_format(conn):
    evidence = [{"file": "test.py", "line": 10}]
    insert_project_skill(conn, 1, "proj1", "python", "Advanced", 0.9, json.dumps(evidence))

    rows = get_project_skills(conn, 1, "proj1")
    assert len(rows) == 1
    skill_name, level, score, evidence_json = rows[0]
    assert skill_name == "python"
    assert level == "Advanced"
    assert score == 0.9
    assert json.loads(evidence_json) == evidence

