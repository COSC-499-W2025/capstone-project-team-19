"""
Tests for chronological skills timeline functionality.
"""

import pytest
import sqlite3
from datetime import datetime
import src.db as db
from src.db.skills import get_skill_events
from src.insights.chronological_skills.skill_timeline import get_skill_timeline


@pytest.fixture
def test_db():
    """Create an in-memory database with required tables for testing."""
    conn = db.connect(":memory:")
    db.init_schema(conn)
    yield conn
    conn.close()


def create_test_user(test_db):
    """Helper: Create a test user and return user_id."""
    return db.get_or_create_user(test_db, "testuser")


def create_project_classification(test_db, user_id, project_name, project_type="code", recorded_at=None):
    """Helper: Create a project and return latest version_key."""
    if recorded_at is None:
        recorded_at = datetime.now().isoformat()

    # record_project_classification returns a version_key in the new schema.
    return db.record_project_classification(
        test_db,
        user_id=user_id,
        zip_path="/path/to/test.zip",
        zip_name="test",
        project_name=project_name,
        classification="individual",
        project_type=project_type,
        when=recorded_at,
    )


def insert_skill(test_db, user_id, project_name, skill_name, level, score):
    """Helper: Insert a skill into project_skills."""
    test_db.execute("""
        INSERT INTO project_skills (user_id, project_name, skill_name, level, score, evidence_json)
        VALUES (?, ?, ?, ?, ?, '[]')
    """, (user_id, project_name, skill_name, level, score))
    test_db.commit()


def test_get_skill_events_with_text_end_date(test_db):
    """Test that text projects use end_date from text_activity_contribution."""
    user_id = create_test_user(test_db)
    classification_id = create_project_classification(test_db, user_id, "TextProject", "text")
    
    # Insert text activity contribution with end_date
    test_db.execute("""
        INSERT INTO text_activity_contribution 
        (version_key, start_date, end_date, duration_days, total_files, classified_files,
         activity_classification_json, timeline_json, activity_counts_json)
        VALUES (?, '2024-01-01', '2024-01-15', 14, 5, 5, '{}', '[]', '{}')
    """, (classification_id,))
    test_db.commit()
    
    insert_skill(test_db, user_id, "TextProject", "writing", "Advanced", 0.9)
    
    rows = get_skill_events(test_db, user_id)
    assert len(rows) == 1
    assert rows[0][0] == "writing"  # skill_name
    assert rows[0][4] == "2024-01-15"  # actual_activity_date (end_date)
    assert rows[0][5] is not None  # recorded_at exists


def test_get_skill_events_with_code_commit_date(test_db):
    """Test that code projects use last_commit_date from github_repo_metrics."""
    user_id = create_test_user(test_db)
    create_project_classification(test_db, user_id, "CodeProject", "code")
    
    # Insert GitHub repo metrics with last_commit_date
    test_db.execute("""
        INSERT INTO github_repo_metrics 
        (user_id, project_name, repo_owner, repo_name, last_commit_date)
        VALUES (?, 'CodeProject', 'owner', 'repo', '2024-02-20')
    """, (user_id,))
    test_db.commit()
    
    insert_skill(test_db, user_id, "CodeProject", "python", "Intermediate", 0.7)
    
    rows = get_skill_events(test_db, user_id)
    assert len(rows) == 1
    assert rows[0][0] == "python"
    assert rows[0][4] == "2024-02-20"  # actual_activity_date (last_commit_date)


def test_get_skill_events_without_activity_date(test_db):
    """Test that projects without activity dates return NULL for actual_activity_date."""
    user_id = create_test_user(test_db)
    create_project_classification(test_db, user_id, "NoDateProject", "code")
    
    insert_skill(test_db, user_id, "NoDateProject", "javascript", "Beginner", 0.5)
    
    rows = get_skill_events(test_db, user_id)
    assert len(rows) == 1
    assert rows[0][0] == "javascript"
    assert rows[0][4] is None  # actual_activity_date is NULL
    assert rows[0][5] is not None  # recorded_at exists


def test_get_skill_events_filters_zero_scores(test_db):
    """Test that skills with score <= 0 are filtered out."""
    user_id = create_test_user(test_db)
    create_project_classification(test_db, user_id, "Project", "code")
    
    insert_skill(test_db, user_id, "Project", "skill1", "Advanced", 0.8)
    insert_skill(test_db, user_id, "Project", "skill2", "Beginner", 0.0)  # Should be filtered
    insert_skill(test_db, user_id, "Project", "skill3", "Intermediate", -0.1)  # Should be filtered
    
    rows = get_skill_events(test_db, user_id)
    assert len(rows) == 1
    assert rows[0][0] == "skill1"


def test_get_skill_events_sorts_by_date(test_db):
    """Test that results are sorted by actual_activity_date, then project_name, then score."""
    user_id = create_test_user(test_db)
    
    # Create projects with different dates
    create_project_classification(test_db, user_id, "ProjectA", "code")
    create_project_classification(test_db, user_id, "ProjectB", "code")
    
    test_db.execute("""
        INSERT INTO github_repo_metrics (user_id, project_name, repo_owner, repo_name, last_commit_date)
        VALUES (?, 'ProjectA', 'owner', 'repo', '2024-01-10'),
               (?, 'ProjectB', 'owner', 'repo', '2024-01-05')
    """, (user_id, user_id))
    test_db.commit()
    
    insert_skill(test_db, user_id, "ProjectA", "skill1", "Advanced", 0.9)
    insert_skill(test_db, user_id, "ProjectB", "skill2", "Intermediate", 0.7)
    
    rows = get_skill_events(test_db, user_id)
    assert len(rows) == 2
    assert rows[0][0] == "skill2"  # Earlier date (2024-01-05)
    assert rows[1][0] == "skill1"  # Later date (2024-01-10)


def test_get_skill_timeline_separates_dated_and_undated(test_db):
    """Test that get_skill_timeline correctly separates dated and undated skills."""
    user_id = create_test_user(test_db)
    
    # Project with activity date
    classification_id = create_project_classification(test_db, user_id, "DatedProject", "text")
    test_db.execute("""
        INSERT INTO text_activity_contribution 
        (version_key, start_date, end_date, duration_days, total_files, classified_files,
         activity_classification_json, timeline_json, activity_counts_json)
        VALUES (?, '2024-01-01', '2024-01-15', 14, 5, 5, '{}', '[]', '{}')
    """, (classification_id,))
    test_db.commit()
    
    # Project without activity date
    create_project_classification(test_db, user_id, "UndatedProject", "code")
    
    insert_skill(test_db, user_id, "DatedProject", "writing", "Advanced", 0.9)
    insert_skill(test_db, user_id, "UndatedProject", "coding", "Intermediate", 0.7)
    
    dated, undated = get_skill_timeline(test_db, user_id)
    
    assert len(dated) == 1
    assert dated[0]["skill_name"] == "writing"
    assert dated[0]["date"] == "2024-01-15"
    
    assert len(undated) == 1
    assert undated[0]["skill_name"] == "coding"
    assert undated[0]["date"] is None


def test_get_skill_timeline_formats_skill_names(test_db):
    """Test that underscores in skill names are replaced with spaces."""
    user_id = create_test_user(test_db)
    create_project_classification(test_db, user_id, "Project", "code")
    
    insert_skill(test_db, user_id, "Project", "data_structures", "Advanced", 0.9)
    insert_skill(test_db, user_id, "Project", "api_and_backend", "Intermediate", 0.7)
    
    dated, undated = get_skill_timeline(test_db, user_id)
    
    # Both should be in undated (no activity dates)
    assert len(undated) == 2
    skill_names = [e["skill_name"] for e in undated]
    assert "data structures" in skill_names
    assert "api and backend" in skill_names
    assert "data_structures" not in skill_names
    assert "api_and_backend" not in skill_names


def test_get_skill_timeline_sorts_dated_by_date(test_db):
    """Test that dated skills are sorted chronologically."""
    user_id = create_test_user(test_db)
    
    # Create projects with different dates
    classification_id1 = create_project_classification(test_db, user_id, "Project1", "text")
    classification_id2 = create_project_classification(test_db, user_id, "Project2", "text")
    
    test_db.execute("""
        INSERT INTO text_activity_contribution 
        (version_key, start_date, end_date, duration_days, total_files, classified_files,
         activity_classification_json, timeline_json, activity_counts_json)
        VALUES 
        (?, '2024-01-01', '2024-01-10', 9, 3, 3, '{}', '[]', '{}'),
        (?, '2024-01-01', '2024-01-05', 4, 2, 2, '{}', '[]', '{}')
    """, (classification_id1, classification_id2))
    test_db.commit()
    
    insert_skill(test_db, user_id, "Project1", "skill1", "Advanced", 0.9)
    insert_skill(test_db, user_id, "Project2", "skill2", "Intermediate", 0.7)
    
    dated, undated = get_skill_timeline(test_db, user_id)
    
    assert len(dated) == 2
    assert dated[0]["skill_name"] == "skill2"  # Earlier date (2024-01-05)
    assert dated[1]["skill_name"] == "skill1"  # Later date (2024-01-10)


def test_get_skill_timeline_empty_results(test_db):
    """Test handling of empty results."""
    user_id = create_test_user(test_db)
    
    dated, undated = get_skill_timeline(test_db, user_id)
    
    assert dated == []
    assert undated == []


def test_get_skill_timeline_only_dated_skills(test_db):
    """Test when all skills have activity dates."""
    user_id = create_test_user(test_db)
    classification_id = create_project_classification(test_db, user_id, "Project", "text")
    
    test_db.execute("""
        INSERT INTO text_activity_contribution 
        (version_key, start_date, end_date, duration_days, total_files, classified_files,
         activity_classification_json, timeline_json, activity_counts_json)
        VALUES (?, '2024-01-01', '2024-01-15', 14, 5, 5, '{}', '[]', '{}')
    """, (classification_id,))
    test_db.commit()
    
    insert_skill(test_db, user_id, "Project", "skill1", "Advanced", 0.9)
    insert_skill(test_db, user_id, "Project", "skill2", "Intermediate", 0.7)
    
    dated, undated = get_skill_timeline(test_db, user_id)
    
    assert len(dated) == 2
    assert len(undated) == 0


def test_get_skill_timeline_only_undated_skills(test_db):
    """Test when no skills have activity dates."""
    user_id = create_test_user(test_db)
    create_project_classification(test_db, user_id, "Project", "code")
    
    insert_skill(test_db, user_id, "Project", "skill1", "Advanced", 0.9)
    insert_skill(test_db, user_id, "Project", "skill2", "Intermediate", 0.7)
    
    dated, undated = get_skill_timeline(test_db, user_id)
    
    assert len(dated) == 0
    assert len(undated) == 2

