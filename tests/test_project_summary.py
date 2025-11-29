import sqlite3
import json
import pytest
from src.models.project_summary import ProjectSummary
from src.db import init_schema, get_or_create_user, record_project_classification, get_classification_id
from src.db.skills import insert_project_skill
from src.db.text_metrics import store_text_offline_metrics
from src.project_analysis import _load_skills_into_summary, _load_text_metrics_into_summary


@pytest.fixture
def conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    yield conn
    conn.close()


@pytest.fixture
def test_user(conn):
    return get_or_create_user(conn, "test-summary-user")


@pytest.fixture
def test_classification(conn, test_user):
    record_project_classification(
        conn, test_user, "/tmp/test.zip", "test", "TestProject", "individual"
    )
    return get_classification_id(conn, test_user, "TestProject")


def test_load_skills_into_summary(conn, test_user):
    summary = ProjectSummary(
        project_name="TestProject",
        project_type="code",
        project_mode="individual"
    )

    insert_project_skill(conn, test_user, "TestProject", "python", "Advanced", 0.9, json.dumps([]))
    insert_project_skill(conn, test_user, "TestProject", "javascript", "Intermediate", 0.6, json.dumps([]))

    _load_skills_into_summary(conn, test_user, "TestProject", summary)

    assert len(summary.skills) == 2
    assert "python" in summary.skills
    assert "javascript" in summary.skills
    assert len(summary.metrics["skills_detailed"]) == 2
    assert summary.metrics["skills_detailed"][0]["skill_name"] == "python"
    assert summary.metrics["skills_detailed"][0]["score"] == 0.9
    assert summary.metrics["skills_detailed"][0]["level"] == "Advanced"
    assert "evidence" not in summary.metrics["skills_detailed"][0]


def test_load_skills_into_summary_handles_empty(conn, test_user):
    summary = ProjectSummary(
        project_name="EmptyProject",
        project_type="code",
        project_mode="individual"
    )

    _load_skills_into_summary(conn, test_user, "EmptyProject", summary)

    assert summary.skills == []
    assert "skills_detailed" not in summary.metrics


def test_load_text_metrics_into_summary(conn, test_user, test_classification):
    summary = ProjectSummary(
        project_name="TestProject",
        project_type="text",
        project_mode="individual"
    )

    store_text_offline_metrics(conn, test_classification, {
        "summary": {
            "total_documents": 2,
            "total_words": 1000,
            "reading_level_average": 12.0,
            "reading_level_label": "College",
        },
        "keywords": [{"word": "test", "score": 0.5}],
    })

    _load_text_metrics_into_summary(conn, test_user, "TestProject", summary)

    assert "text" in summary.metrics
    assert summary.metrics["text"]["non_llm"]["doc_count"] == 2
    assert summary.metrics["text"]["non_llm"]["total_words"] == 1000


def test_load_text_metrics_into_summary_skips_code_projects(conn, test_user):
    summary = ProjectSummary(
        project_name="CodeProject",
        project_type="code",
        project_mode="individual"
    )

    _load_text_metrics_into_summary(conn, test_user, "CodeProject", summary)

    assert "text" not in summary.metrics


def test_load_text_metrics_into_summary_handles_missing_metrics(conn, test_user, test_classification):
    summary = ProjectSummary(
        project_name="TestProject",
        project_type="text",
        project_mode="individual"
    )

    _load_text_metrics_into_summary(conn, test_user, "TestProject", summary)

    assert "text" not in summary.metrics

