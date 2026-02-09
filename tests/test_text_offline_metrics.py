import json
import db
from src.db.text_metrics import get_text_non_llm_metrics


def _create_classification(conn, user_id, project_name="OfflineText"):
    zip_path = "/tmp/sample.zip"
    zip_name = "sample"
    db.record_project_classification(
        conn=conn,
        user_id=user_id,
        zip_path=zip_path,
        zip_name=zip_name,
        project_name=project_name,
        classification="individual",
    )
    return db.get_classification_id(conn, user_id, project_name)


def _fetch_metrics(conn, classification_id):
    return conn.execute(
        """
        SELECT doc_count,
               total_words,
               reading_level_avg,
               reading_level_label,
               keywords_json
        FROM non_llm_text
        WHERE version_key = ?
        """,
        (classification_id,),
    ).fetchone()


def test_store_text_offline_metrics_upserts(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "metrics-user")
    classification_id = _create_classification(conn, user_id)

    metrics_payload = {
        "summary": {
            "total_documents": 3,
            "total_words": 1500,
            "reading_level_average": 10.2,
            "reading_level_label": "College",
        },
        "keywords": [
            {"word": "analysis", "score": 0.6},
            {"word": "pipeline", "score": 0.4},
        ],
    }

    db.store_text_offline_metrics(conn, classification_id, metrics_payload)

    row = _fetch_metrics(conn, classification_id)
    assert row[0] == 3
    assert row[1] == 1500
    assert row[2] == 10.2
    assert row[3] == "College"
    assert json.loads(row[4]) == metrics_payload["keywords"]

    # Update to ensure upsert path works
    metrics_payload["summary"]["total_documents"] = 4
    db.store_text_offline_metrics(conn, classification_id, metrics_payload)

    updated = _fetch_metrics(conn, classification_id)
    assert updated[0] == 4


def test_store_text_offline_metrics_preserves_existing_fields(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "metrics-preserve-user")
    classification_id = _create_classification(conn, user_id)

    original_keywords = [{"word": "analysis", "score": 0.9}]
    db.store_text_offline_metrics(
        conn,
        classification_id,
        {
            "summary": {"total_documents": 2},
            "keywords": original_keywords,
        },
    )

    # Second call omits keywords; existing ones should remain.
    db.store_text_offline_metrics(
        conn,
        classification_id,
        {
            "summary": {"total_documents": 3},
        },
    )

    row = _fetch_metrics(conn, classification_id)
    assert row[0] == 3  # doc_count updated
    assert json.loads(row[4]) == original_keywords  # keywords preserved


def test_store_text_offline_metrics_requires_classification(shared_db):
    conn = db.connect()
    payload = {"summary": {"total_documents": 1}}
    db.store_text_offline_metrics(conn, None, payload)

    count = conn.execute("SELECT COUNT(*) FROM non_llm_text").fetchone()[0]
    assert count == 0


def test_store_text_offline_metrics_handles_missing_payload(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "metrics-empty-user")
    classification_id = _create_classification(conn, user_id)

    db.store_text_offline_metrics(conn, classification_id, None)
    assert _fetch_metrics(conn, classification_id) is None


def test_get_text_non_llm_metrics(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "get-metrics-user")
    classification_id = _create_classification(conn, user_id, "TestProject")

    metrics_payload = {
        "summary": {
            "total_documents": 2,
            "total_words": 1000,
            "reading_level_average": 12.5,
            "reading_level_label": "College",
        },
        "keywords": [{"word": "test", "score": 0.8}],
    }
    db.store_text_offline_metrics(conn, classification_id, metrics_payload)

    result = get_text_non_llm_metrics(conn, classification_id)
    assert result is not None
    assert result["doc_count"] == 2
    assert result["total_words"] == 1000
    assert result["reading_level_avg"] == 12.5
    assert result["reading_level_label"] == "College"
    assert result["keywords"] == [{"word": "test", "score": 0.8}]


def test_get_text_non_llm_metrics_returns_none_when_missing(shared_db):
    conn = db.connect()
    user_id = db.get_or_create_user(conn, "get-metrics-missing-user")
    classification_id = _create_classification(conn, user_id, "NoMetricsProject")

    result = get_text_non_llm_metrics(conn, classification_id)
    assert result is None