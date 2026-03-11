import sqlite3

from src.db import init_schema, get_or_create_user
from src.db.user_education import (
    list_user_education_entries,
    add_user_education_entry,
    delete_user_education_entry,
)


def make_conn():
    conn = sqlite3.connect(":memory:")
    init_schema(conn)
    return conn


def test_list_user_education_entries_empty_for_new_user():
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    entries = list_user_education_entries(conn, user_id)

    assert entries == []


def test_user_education_round_trip():
    """
    Covers add/list/delete for both education and certificate entries.
    """
    conn = make_conn()
    user_id = get_or_create_user(conn, "alice")

    edu_id = add_user_education_entry(
        conn,
        user_id,
        entry_type="education",
        title="BSc in Computer Science",
        organization="UBCO",
        date_text="2022 - 2026",
        description="Major in data science.",
    )

    cert_id = add_user_education_entry(
        conn,
        user_id,
        entry_type="certificate",
        title="AWS Cloud Practitioner",
        organization="Amazon Web Services",
        date_text="2025",
        description="Foundational cloud certification.",
    )

    entries = list_user_education_entries(conn, user_id)

    assert len(entries) == 2
    assert entries[0]["entry_id"] == edu_id
    assert entries[0]["entry_type"] == "education"
    assert entries[1]["entry_id"] == cert_id
    assert entries[1]["entry_type"] == "certificate"

    assert delete_user_education_entry(conn, user_id, edu_id) is True
    assert delete_user_education_entry(conn, user_id, cert_id) is True
    assert list_user_education_entries(conn, user_id) == []