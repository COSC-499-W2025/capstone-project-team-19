import json
import db


def _create_classification(conn, user_id, project_name="CodeProject"):
    zip_path = "/tmp/code_sample.zip"
    zip_name = "code_sample"
    db.record_project_classification(
        conn=conn,
        user_id=user_id,
        zip_path=zip_path,
        zip_name=zip_name,
        project_name=project_name,
        classification="individual",
    )
    return db.get_classification_id(conn, user_id, project_name)


def _fetch_complexity_metrics(conn, classification_id):
    return conn.execute(
        """
        SELECT total_files,
               total_lines,
               total_code_lines,
               total_comments,
               comment_ratio,
               total_functions,
               avg_complexity,
               avg_maintainability,
               functions_needing_refactor,
               high_complexity_files,
               low_maintainability_files,
               radon_details_json,
               lizard_details_json
        FROM non_llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()


def _fetch_llm_metrics(conn, classification_id):
    return conn.execute(
        """
        SELECT project_summary
        FROM llm_code_individual
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()


# ========== Code Complexity Metrics Tests ==========

def test_store_code_complexity_metrics_inserts(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-metrics-user")
    classification_id = _create_classification(conn, user_id)

    complexity_summary = {
        "total_files": 10,
        "total_lines": 5000,
        "total_code": 4200,
        "total_comments": 800,
        "total_functions": 45,
        "avg_complexity": 7.5,
        "avg_maintainability": 65.3,
        "functions_needing_refactor": 3,
        "high_complexity_files": 2,
        "low_maintainability_files": 1,
        "radon_details": {"A": 5, "B": 3, "C": 2},
        "lizard_details": {"nloc": 4200, "avg_ccn": 7.5}
    }

    db.store_code_complexity_metrics(conn, classification_id, complexity_summary)

    row = _fetch_complexity_metrics(conn, classification_id)
    assert row[0] == 10  # total_files
    assert row[1] == 5000  # total_lines
    assert row[2] == 4200  # total_code_lines
    assert row[3] == 800  # total_comments
    assert row[4] == 16.0  # comment_ratio (800/5000 * 100)
    assert row[5] == 45  # total_functions
    assert row[6] == 7.5  # avg_complexity
    assert row[7] == 65.3  # avg_maintainability
    assert row[8] == 3  # functions_needing_refactor
    assert row[9] == 2  # high_complexity_files
    assert row[10] == 1  # low_maintainability_files
    assert json.loads(row[11]) == {"A": 5, "B": 3, "C": 2}  # radon_details
    assert json.loads(row[12]) == {"nloc": 4200, "avg_ccn": 7.5}  # lizard_details


def test_store_code_complexity_metrics_updates(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-update-user")
    classification_id = _create_classification(conn, user_id)

    # Initial insert
    initial_summary = {
        "total_files": 5,
        "total_lines": 2000,
        "total_code": 1800,
        "total_comments": 200,
        "total_functions": 20,
        "avg_complexity": 5.0,
        "avg_maintainability": 70.0,
        "functions_needing_refactor": 1,
        "high_complexity_files": 0,
        "low_maintainability_files": 0,
    }
    db.store_code_complexity_metrics(conn, classification_id, initial_summary)

    # Update with new data
    updated_summary = {
        "total_files": 8,
        "total_lines": 3500,
        "total_code": 3000,
        "total_comments": 500,
        "total_functions": 35,
        "avg_complexity": 6.2,
        "avg_maintainability": 68.5,
        "functions_needing_refactor": 2,
        "high_complexity_files": 1,
        "low_maintainability_files": 0,
    }
    db.store_code_complexity_metrics(conn, classification_id, updated_summary)

    row = _fetch_complexity_metrics(conn, classification_id)
    assert row[0] == 8  # total_files updated
    assert row[1] == 3500  # total_lines updated
    assert row[5] == 35  # total_functions updated


def test_store_code_complexity_metrics_calculates_comment_ratio(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-ratio-user")
    classification_id = _create_classification(conn, user_id)

    complexity_summary = {
        "total_files": 1,
        "total_lines": 1000,
        "total_code": 750,
        "total_comments": 250,
        "total_functions": 10,
        "avg_complexity": 5.0,
        "avg_maintainability": 75.0,
        "functions_needing_refactor": 0,
        "high_complexity_files": 0,
        "low_maintainability_files": 0,
    }

    db.store_code_complexity_metrics(conn, classification_id, complexity_summary)

    row = _fetch_complexity_metrics(conn, classification_id)
    assert row[4] == 25.0  # comment_ratio should be 250/1000 * 100 = 25.0


def test_store_code_complexity_metrics_handles_zero_lines(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-zero-user")
    classification_id = _create_classification(conn, user_id)

    complexity_summary = {
        "total_files": 0,
        "total_lines": 0,
        "total_code": 0,
        "total_comments": 0,
        "total_functions": 0,
        "avg_complexity": 0,
        "avg_maintainability": 0,
        "functions_needing_refactor": 0,
        "high_complexity_files": 0,
        "low_maintainability_files": 0,
    }

    db.store_code_complexity_metrics(conn, classification_id, complexity_summary)

    row = _fetch_complexity_metrics(conn, classification_id)
    assert row[4] == 0  # comment_ratio should be 0 when total_lines is 0


def test_store_code_complexity_metrics_requires_classification(shared_db):
    conn = db.connect()
    complexity_summary = {"total_files": 1}
    db.store_code_complexity_metrics(conn, None, complexity_summary)

    count = conn.execute("SELECT COUNT(*) FROM non_llm_code_individual").fetchone()[0]
    assert count == 0


def test_store_code_complexity_metrics_handles_missing_payload(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-empty-user")
    classification_id = _create_classification(conn, user_id)

    db.store_code_complexity_metrics(conn, classification_id, None)
    assert _fetch_complexity_metrics(conn, classification_id) is None


def test_get_code_complexity_metrics_returns_correct_data(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-get-user")
    classification_id = _create_classification(conn, user_id)

    complexity_summary = {
        "total_files": 12,
        "total_lines": 6000,
        "total_code": 5000,
        "total_comments": 1000,
        "total_functions": 50,
        "avg_complexity": 8.0,
        "avg_maintainability": 60.0,
        "functions_needing_refactor": 5,
        "high_complexity_files": 3,
        "low_maintainability_files": 2,
        "radon_details": {"A": 10, "B": 2},
        "lizard_details": {"nloc": 5000}
    }

    db.store_code_complexity_metrics(conn, classification_id, complexity_summary)
    result = db.get_code_complexity_metrics(conn, classification_id)

    assert result is not None
    assert result["total_files"] == 12
    assert result["total_lines"] == 6000
    assert result["avg_complexity"] == 8.0
    assert result["radon_details"] == {"A": 10, "B": 2}
    assert result["lizard_details"] == {"nloc": 5000}


def test_get_code_complexity_metrics_returns_none_when_not_found(shared_db):
    conn = db.connect()
    result = db.get_code_complexity_metrics(conn, 99999)
    assert result is None


# ========== Code LLM Metrics Tests ==========

def test_store_code_llm_metrics_inserts(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-llm-user")
    classification_id = _create_classification(conn, user_id)

    project_summary = "This is a Python web application using Flask framework."

    db.store_code_llm_metrics(conn, classification_id, project_summary)

    row = _fetch_llm_metrics(conn, classification_id)
    assert row[0] == project_summary


def test_store_code_llm_metrics_updates(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-llm-update-user")
    classification_id = _create_classification(conn, user_id)

    initial_summary = "Initial project summary."
    db.store_code_llm_metrics(conn, classification_id, initial_summary)

    updated_summary = "Updated project summary with more details."
    db.store_code_llm_metrics(conn, classification_id, updated_summary)

    row = _fetch_llm_metrics(conn, classification_id)
    assert row[0] == updated_summary


def test_store_code_llm_metrics_requires_classification(shared_db):
    conn = db.connect()
    db.store_code_llm_metrics(conn, None, "Some summary")

    count = conn.execute("SELECT COUNT(*) FROM llm_code_individual").fetchone()[0]
    assert count == 0


def test_store_code_llm_metrics_requires_summary(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-llm-no-summary-user")
    classification_id = _create_classification(conn, user_id)

    db.store_code_llm_metrics(conn, classification_id, None)

    assert _fetch_llm_metrics(conn, classification_id) is None


def test_get_code_llm_metrics_returns_correct_data(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "code-llm-get-user")
    classification_id = _create_classification(conn, user_id)

    project_summary = "A comprehensive Django application for e-commerce."
    db.store_code_llm_metrics(conn, classification_id, project_summary)

    result = db.get_code_llm_metrics(conn, classification_id)

    assert result is not None
    assert result["classification_id"] == classification_id
    assert result["project_summary"] == project_summary
    assert "processed_at" in result


def test_get_code_llm_metrics_returns_none_when_not_found(shared_db):
    conn = db.connect()
    result = db.get_code_llm_metrics(conn, 99999)
    assert result is None
