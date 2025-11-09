import json
import db


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

    row = conn.execute(
        """
        SELECT doc_count, total_words, reading_level_avg, reading_level_label, keywords_json
        FROM text_offline_metrics
        WHERE classification_id = ?
        """,
        (classification_id,),
    ).fetchone()

    assert row[0] == 3
    assert row[1] == 1500
    assert row[2] == 10.2
    assert row[3] == "College"
    assert json.loads(row[4]) == metrics_payload["keywords"]

    # Update to ensure upsert path works
    metrics_payload["summary"]["total_documents"] = 4
    db.store_text_offline_metrics(conn, classification_id, metrics_payload)

    updated = conn.execute(
        "SELECT doc_count FROM text_offline_metrics WHERE classification_id = ?",
        (classification_id,),
    ).fetchone()
    assert updated[0] == 4
